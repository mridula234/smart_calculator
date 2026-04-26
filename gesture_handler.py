"""
gesture_handler.py
───────────────────
Webcam-based hand gesture detection using MediaPipe 0.10.30+ (Tasks API).
Counts raised fingers and detects horizontal swipes → calculator actions.

Dependencies:
    pip install opencv-python mediapipe pillow
"""

import threading
import time
from collections import deque
from typing import Callable, Optional

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[GestureHandler] WARNING: opencv-python not installed.")

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
    print("[GestureHandler] WARNING: mediapipe not installed.")

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

TIP_IDS = [4, 8, 12, 16, 20]
PIP_IDS = [3, 6, 10, 14, 18]


class GestureHandler:
    OPERATORS = ["+", "-", "*", "/"]

    def __init__(self, callback: Callable[[str, Optional[object]], None]):
        self.callback      = callback
        self.running       = False
        self._thread: Optional[threading.Thread] = None
        self._stop_evt     = threading.Event()
        self._op_index     = 0
        self._frame_cb: Optional[Callable] = None
        self._x_history: deque = deque(maxlen=10)
        self._last_action_time = 0.0
        self._cooldown         = 1.2
        self._detector         = None

    def start(self, frame_callback: Optional[Callable] = None):
        if not (CV2_AVAILABLE and MP_AVAILABLE):
            self.callback("error", "opencv / mediapipe not installed")
            return
        if self.running:
            return
        self._frame_cb = frame_callback
        self.running   = True
        self._stop_evt.clear()
        self._thread   = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self._stop_evt.set()

    def _make_detector(self):
        # Strategy 1: legacy solutions (mediapipe < 0.10)
        try:
            import importlib
            sol = importlib.import_module("mediapipe.python.solutions.hands")
            hands = sol.Hands(max_num_hands=1,
                              min_detection_confidence=0.7,
                              min_tracking_confidence=0.6)
            def detect(rgb):
                r = hands.process(rgb)
                if not r.multi_hand_landmarks:
                    return []
                return [[(lm.x, lm.y, lm.z) for lm in h.landmark]
                        for h in r.multi_hand_landmarks]
            print("[GestureHandler] Using legacy solutions API")
            return detect
        except Exception:
            pass

        # Strategy 2: Tasks API with downloaded model
        try:
            import urllib.request, os, tempfile
            model_path = os.path.join(tempfile.gettempdir(), "hand_landmarker.task")
            if not os.path.exists(model_path):
                print("[GestureHandler] Downloading hand landmark model (~8 MB)...")
                url = ("https://storage.googleapis.com/mediapipe-models/"
                       "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
                urllib.request.urlretrieve(url, model_path)
                print("[GestureHandler] Model downloaded.")

            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import (
                HandLandmarker, HandLandmarkerOptions, RunningMode)

            opts = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,
                num_hands=1)
            lm_model = HandLandmarker.create_from_options(opts)

            def detect(rgb):
                img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = lm_model.detect(img)
                if not result.hand_landmarks:
                    return []
                return [[(lm.x, lm.y, lm.z) for lm in h]
                        for h in result.hand_landmarks]
            print("[GestureHandler] Using Tasks API")
            return detect
        except Exception as e:
            print(f"[GestureHandler] Tasks API failed: {e}")

        self.callback("error", "Hand detection unavailable")
        return lambda rgb: []

    def _capture_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.callback("error", "Cannot open webcam")
            self.running = False
            return

        detector = self._make_detector()

        while self.running and not self._stop_evt.is_set():
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                hands = detector(rgb)
                if hands:
                    lm      = hands[0]
                    fingers = self._count_fingers(lm)
                    swipe   = self._detect_swipe(lm[0][0])

                    h, w = frame.shape[:2]
                    for tip in TIP_IDS:
                        cx, cy = int(lm[tip][0]*w), int(lm[tip][1]*h)
                        cv2.circle(frame, (cx, cy), 8, (100, 255, 100), -1)
                    cv2.putText(frame, f"Fingers: {fingers}", (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,100), 2)

                    if swipe and self._can_act():
                        self._last_action_time = time.time()
                        if swipe == "right":
                            self._op_index = (self._op_index+1) % len(self.OPERATORS)
                            self.callback("operator", self.OPERATORS[self._op_index])
                        else:
                            self.callback("del", None)
                    elif fingers > 0 and self._can_act():
                        self._last_action_time = time.time()
                        self.callback("eval" if fingers == 5 else "digit",
                                      None if fingers == 5 else fingers)
            except Exception as e:
                cv2.putText(frame, str(e)[:40], (10,40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

            if self._frame_cb and PIL_AVAILABLE:
                try:
                    small  = cv2.resize(frame, (380, 220))
                    img_tk = ImageTk.PhotoImage(
                        Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB)))
                    self._frame_cb(img_tk)
                except Exception:
                    pass

        cap.release()
        self.running = False

    def _count_fingers(self, lm) -> int:
        count = 0
        if lm[TIP_IDS[0]][0] < lm[TIP_IDS[0]-1][0]:
            count += 1
        for i in range(1, 5):
            if lm[TIP_IDS[i]][1] < lm[PIP_IDS[i]][1]:
                count += 1
        return count

    def _detect_swipe(self, x: float) -> Optional[str]:
        self._x_history.append(x)
        if len(self._x_history) < 8:
            return None
        delta = self._x_history[-1] - self._x_history[0]
        if delta > 0.18:
            self._x_history.clear()
            return "right"
        if delta < -0.18:
            self._x_history.clear()
            return "left"
        return None

    def _can_act(self) -> bool:
        return (time.time() - self._last_action_time) > self._cooldown