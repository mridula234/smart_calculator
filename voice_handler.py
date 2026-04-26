"""
voice_handler.py
─────────────────
Listens to the microphone in a background thread,
converts speech → text, then parses it into calculator actions.

Dependency:
    pip install SpeechRecognition pyaudio
"""

import re
import threading
from typing import Callable, Optional

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("[VoiceHandler] WARNING: SpeechRecognition not installed. "
          "Run: pip install SpeechRecognition pyaudio")


# ── Number word → digit mapping ───────────────────────────────────────────────
NUM_WORDS = {
    "zero": 0,  "one": 1,   "two": 2,   "three": 3, "four": 4,
    "five": 5,  "six": 6,   "seven": 7, "eight": 8, "nine": 9,
    "ten": 10,  "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
}

OP_WORDS = {
    r"\bplus\b":               "+",
    r"\badd\b":                "+",
    r"\bminus\b":              "-",
    r"\bsubtract\b":           "-",
    r"\btimes\b":              "*",
    r"\bmultiply\b":           "*",
    r"\bmultiplied by\b":      "*",
    r"\bdivide\b":             "/",
    r"\bdivided by\b":         "/",
    r"\bover\b":               "/",
    r"\bmodulo\b":             "%",
    r"\bremainder\b":          "%",
}

STOP_WORDS = re.compile(
    r"\b(what is|calculate|compute|tell me|equals|equal to|please)\b", re.I
)


class VoiceHandler:
    """
    Manages speech recognition in a background daemon thread.

    callback(action, value):
        action = "expr"   → value is a math expression string e.g. "5+8"
        action = "eval"   → trigger equals
        action = "clear"  → clear display
        action = "error"  → value is an error message string
    """

    def __init__(self, callback: Callable[[str, Optional[str]], None]):
        self.callback  = callback
        self.running   = False
        self._thread: Optional[threading.Thread] = None
        self._stop_evt = threading.Event()

        if SR_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold        = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold         = 0.8

    # ── Public ────────────────────────────────
    def start(self):
        if not SR_AVAILABLE:
            self.callback("error", "SpeechRecognition not installed")
            return
        if self.running:
            return
        self.running = True
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self._stop_evt.set()

    # ── Background thread ─────────────────────
    def _listen_loop(self):
        try:
            mic = sr.Microphone()
        except OSError:
            self.callback("error", "No microphone found")
            self.running = False
            return

        with mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.5)

        while self.running and not self._stop_evt.is_set():
            try:
                with mic as source:
                    audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=6)
                text = self._recognizer.recognize_google(audio)
                print(f"[Voice] Heard: {text}")
                self._parse_and_dispatch(text)
            except sr.WaitTimeoutError:
                pass                        # silence — keep listening
            except sr.UnknownValueError:
                self.callback("error", "Could not understand audio")
            except sr.RequestError as e:
                self.callback("error", f"API error: {e}")
                self.running = False

    # ── NLP parser ────────────────────────────
    def _parse_and_dispatch(self, text: str):
        t = text.lower().strip()

        # ── Control commands ──
        if re.search(r"\b(clear|reset|delete all)\b", t):
            self.callback("clear", "clear")
            return
        if re.search(r"\b(equals?|result|calculate|compute)\s*$", t):
            self.callback("eval", "equals")
            return

        # ── Remove filler words ──
        t = STOP_WORDS.sub("", t).strip()

        # ── Operator words → symbols ──
        for pattern, symbol in OP_WORDS.items():
            t = re.sub(pattern, f" {symbol} ", t, flags=re.I)

        # ── Number words → digits ──
        for word, digit in sorted(NUM_WORDS.items(), key=lambda x: -len(x[0])):
            t = re.sub(rf"\b{word}\b", str(digit), t, flags=re.I)

        # ── Collapse whitespace ──
        t = re.sub(r"\s+", " ", t).strip()

        # ── Remove any remaining non-math characters ──
        expr = re.sub(r"[^0-9+\-*/.%() ]", "", t)
        expr = re.sub(r"\s+", "", expr).strip()

        if expr:
            self.callback("expr", expr)
        else:
            self.callback("error", f"Couldn't parse: '{text}'")
