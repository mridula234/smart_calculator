"""
Smart Multimodal Calculator
============================
Modes: Basic (buttons) | Voice (SpeechRecognition) | Gesture (MediaPipe + OpenCV)

Install dependencies:
    pip install opencv-python mediapipe SpeechRecognition pyaudio pillow

Run:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import threading

from voice_handler import VoiceHandler
from gesture_handler import GestureHandler
from calculator_logic import CalculatorLogic


# ─────────────────────────────────────────────
#  Colour palette
# ─────────────────────────────────────────────
COLORS = {
    "bg":        "#0d0d0f",
    "bg2":       "#161618",
    "bg3":       "#1e1e22",
    "bg4":       "#252529",
    "accent":    "#6c63ff",
    "accent2":   "#a78bfa",
    "green":     "#22c55e",
    "red":       "#ef4444",
    "amber":     "#f59e0b",
    "text":      "#f4f4f5",
    "muted":     "#71717a",
    "border":    "#2e2e35",
}


# ─────────────────────────────────────────────
#  Main Application Window
# ─────────────────────────────────────────────
class SmartCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Multimodal Calculator")
        self.geometry("500x860")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])

        # Core components
        self.logic   = CalculatorLogic()
        self.voice   = VoiceHandler(callback=self._on_voice_result)
        self.gesture = GestureHandler(callback=self._on_gesture_result)

        self._current_mode = "basic"
        self._build_ui()

    # ── UI Construction ──────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_display()
        self._build_mode_tabs()
        self._build_basic_panel()
        self._build_voice_panel()
        self._build_gesture_panel()
        self._show_panel("basic")

    def _build_header(self):
        hdr = tk.Frame(self, bg="#16213e", height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="SMART MULTIMODAL CALCULATOR",
            bg="#16213e", fg=COLORS["accent2"],
            font=("Courier", 9, "bold")
        ).pack(side="left", padx=16, pady=14)
        tk.Label(
            hdr, text="● ACTIVE",
            bg="#16213e", fg=COLORS["green"],
            font=("Courier", 8)
        ).pack(side="right", padx=16)

    def _build_display(self):
        disp = tk.Frame(self, bg=COLORS["bg2"], pady=12)
        disp.pack(fill="x")

        self.expr_var   = tk.StringVar(value="0")
        self.result_var = tk.StringVar(value="0")

        tk.Label(
            disp, textvariable=self.expr_var,
            bg=COLORS["bg2"], fg=COLORS["muted"],
            font=("Courier", 11), anchor="e", padx=20
        ).pack(fill="x")

        tk.Label(
            disp, textvariable=self.result_var,
            bg=COLORS["bg2"], fg=COLORS["text"],
            font=("Courier", 36, "bold"), anchor="e", padx=20
        ).pack(fill="x")

    def _build_mode_tabs(self):
        tab_frame = tk.Frame(self, bg=COLORS["bg3"])
        tab_frame.pack(fill="x")

        self._tab_buttons = {}
        for mode, label in [("basic", "⌨  Basic"), ("voice", "🎤  Voice"), ("gesture", "✋  Gesture")]:
            btn = tk.Button(
                tab_frame, text=label,
                bg=COLORS["bg3"], fg=COLORS["muted"],
                font=("Helvetica", 10), bd=0, relief="flat",
                padx=10, pady=8, cursor="hand2",
                command=lambda m=mode: self._switch_mode(m)
            )
            btn.pack(side="left", expand=True, fill="x")
            self._tab_buttons[mode] = btn

    def _switch_mode(self, mode: str):
        # Stop any running background processes
        if self._current_mode == "voice":
            self.voice.stop()
        if self._current_mode == "gesture":
            self.gesture.stop()

        self._current_mode = mode
        self._show_panel(mode)

        # Update tab colours
        for m, btn in self._tab_buttons.items():
            btn.config(
                fg=COLORS["accent2"] if m == mode else COLORS["muted"],
                bg=COLORS["bg4"]     if m == mode else COLORS["bg3"],
            )

    def _show_panel(self, mode: str):
        for panel in [self.basic_panel, self.voice_panel, self.gesture_panel]:
            panel.pack_forget()
        {
            "basic":   self.basic_panel,
            "voice":   self.voice_panel,
            "gesture": self.gesture_panel,
        }[mode].pack(fill="both", expand=True)

    # ── Basic Keypad ─────────────────────────
    def _build_basic_panel(self):
        self.basic_panel = tk.Frame(self, bg=COLORS["bg"])
        keys = [
            ("C",   COLORS["red"],    1),  ("⌫",  COLORS["amber"], 1),
            ("%",   COLORS["muted"],  1),  ("÷",  COLORS["accent2"],1),
            ("7",   COLORS["text"],   1),  ("8",  COLORS["text"],   1),
            ("9",   COLORS["text"],   1),  ("×",  COLORS["accent2"],1),
            ("4",   COLORS["text"],   1),  ("5",  COLORS["text"],   1),
            ("6",   COLORS["text"],   1),  ("−",  COLORS["accent2"],1),
            ("1",   COLORS["text"],   1),  ("2",  COLORS["text"],   1),
            ("3",   COLORS["text"],   1),  ("+",  COLORS["accent2"],1),
            ("0",   COLORS["text"],   2),  (".",  COLORS["text"],   1),
            ("=",   COLORS["accent"], 1),
        ]

        grid = tk.Frame(self.basic_panel, bg=COLORS["border"])
        grid.pack(fill="both", expand=True, padx=1, pady=1)

        col, row = 0, 0
        for (label, color, span) in keys:
            btn = tk.Button(
                grid, text=label,
                bg=COLORS["bg3"], fg=color,
                font=("Helvetica", 18), bd=0, relief="flat",
                padx=0, pady=0, cursor="hand2",
                activebackground=COLORS["bg4"], activeforeground=color,
                command=lambda k=label: self._on_key(k)
            )
            btn.grid(row=row, column=col, columnspan=span,
                     sticky="nsew", padx=1, pady=1, ipadx=0, ipady=18)
            col += span
            if col >= 4:
                col = 0
                row += 1

        for c in range(4):
            grid.columnconfigure(c, weight=1)
        for r in range(row + 1):
            grid.rowconfigure(r, weight=1)

    def _on_key(self, key: str):
        # Map display symbols back to logic symbols
        key = {"÷": "/", "×": "*", "−": "-", "⌫": "DEL"}.get(key, key)
        self.logic.press(key)
        self._refresh_display()

    def _refresh_display(self):
        self.expr_var.set(self.logic.expression or "0")
        self.result_var.set(self.logic.evaluate_preview())

    # ── Voice Panel ──────────────────────────
    def _build_voice_panel(self):
        self.voice_panel = tk.Frame(self, bg=COLORS["bg2"])

        tk.Label(
            self.voice_panel,
            text="🎤  Voice Mode",
            bg=COLORS["bg2"], fg=COLORS["accent2"],
            font=("Helvetica", 14, "bold")
        ).pack(pady=(30, 6))

        tk.Label(
            self.voice_panel,
            text='Say: "five plus eight" · "nine times seven"\n"clear" · "equals"',
            bg=COLORS["bg2"], fg=COLORS["muted"],
            font=("Helvetica", 10), justify="center"
        ).pack(pady=(0, 20))

        self.voice_status = tk.StringVar(value="Press the button to start")
        tk.Label(
            self.voice_panel, textvariable=self.voice_status,
            bg=COLORS["bg2"], fg=COLORS["green"],
            font=("Courier", 11), wraplength=360, justify="center"
        ).pack(pady=10)

        self.mic_btn = tk.Button(
            self.voice_panel, text="🎤  Start Listening",
            bg=COLORS["accent"], fg="white",
            font=("Helvetica", 13, "bold"),
            bd=0, relief="flat", padx=20, pady=12,
            cursor="hand2",
            command=self._toggle_voice
        )
        self.mic_btn.pack(pady=20)

        tk.Label(
            self.voice_panel,
            text="Powered by SpeechRecognition + Google STT",
            bg=COLORS["bg2"], fg=COLORS["muted"],
            font=("Helvetica", 8)
        ).pack(side="bottom", pady=10)

    def _toggle_voice(self):
        if self.voice.running:
            self.voice.stop()
            self.mic_btn.config(text="🎤  Start Listening", bg=COLORS["accent"])
            self.voice_status.set("Stopped.")
        else:
            self.mic_btn.config(text="⏹  Stop Listening", bg=COLORS["red"])
            self.voice_status.set("Listening…")
            self.voice.start()

    def _on_voice_result(self, action: str, value=None):
        """Called from voice thread — schedule UI update on main thread."""
        self.after(0, self._apply_voice, action, value)

    def _apply_voice(self, action: str, value=None):
        if action == "clear":
            self.logic.press("C")
        elif action == "eval":
            self.logic.press("=")
        elif action == "expr" and value:
            self.logic.set_expression(value)
        elif action == "error":
            self.voice_status.set(f"⚠ {value}")
            return

        self.voice_status.set(f"Heard: {value or action}")
        self._refresh_display()

    # ── Gesture Panel ────────────────────────
    def _build_gesture_panel(self):
        self.gesture_panel = tk.Frame(self, bg=COLORS["bg2"])

        tk.Label(
            self.gesture_panel,
            text="✋  Gesture Mode",
            bg=COLORS["bg2"], fg=COLORS["accent2"],
            font=("Helvetica", 14, "bold")
        ).pack(pady=(20, 4))

        # Live camera feed label
        self.cam_label = tk.Label(
            self.gesture_panel,
            bg=COLORS["bg3"], text="[ Camera Feed ]",
            fg=COLORS["muted"], width=56, height=12,
            font=("Courier", 10)
        )
        self.cam_label.pack(pady=10)

        self.gesture_status = tk.StringVar(value="Press Start to activate camera")
        tk.Label(
            self.gesture_panel, textvariable=self.gesture_status,
            bg=COLORS["bg2"], fg=COLORS["green"],
            font=("Courier", 11), wraplength=360
        ).pack(pady=6)

        # Reference card
        ref = tk.Frame(self.gesture_panel, bg=COLORS["bg3"], padx=14, pady=10)
        ref.pack(fill="x", padx=20, pady=6)
        for gesture_txt, meaning in [
            ("☝  1 finger",  "→ digit 1"),
            ("✌  2 fingers", "→ digit 2"),
            ("🖐  5 fingers", "→  equals (=)"),
            ("👉  Swipe right","→ next operator"),
            ("👈  Swipe left", "→ backspace"),
        ]:
            row = tk.Frame(ref, bg=COLORS["bg3"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=gesture_txt, bg=COLORS["bg3"],
                     fg=COLORS["text"], font=("Helvetica", 10), width=18, anchor="w").pack(side="left")
            tk.Label(row, text=meaning,    bg=COLORS["bg3"],
                     fg=COLORS["muted"], font=("Helvetica", 10)).pack(side="left")

        self.gest_btn = tk.Button(
            self.gesture_panel, text="▶  Start Gesture Mode",
            bg=COLORS["green"], fg="white",
            font=("Helvetica", 12, "bold"),
            bd=0, relief="flat", padx=16, pady=10,
            cursor="hand2",
            command=self._toggle_gesture
        )
        self.gest_btn.pack(pady=14)

    def _toggle_gesture(self):
        if self.gesture.running:
            self.gesture.stop()
            self.gest_btn.config(text="▶  Start Gesture Mode", bg=COLORS["green"])
            self.gesture_status.set("Camera stopped.")
        else:
            self.gest_btn.config(text="⏹  Stop Gesture Mode", bg=COLORS["red"])
            self.gesture_status.set("Camera active — show your hand!")
            self.gesture.start(frame_callback=self._update_cam_frame)

    def _update_cam_frame(self, img_tk):
        """Receive a PhotoImage from gesture thread and update label."""
        self.after(0, lambda: self.cam_label.config(image=img_tk, text=""))
        self.cam_label.image = img_tk  # prevent GC

    def _on_gesture_result(self, action: str, value=None):
        self.after(0, self._apply_gesture, action, value)

    def _apply_gesture(self, action: str, value=None):
        if action == "digit":
            self.logic.press(str(value))
        elif action == "operator":
            self.logic.press(value)
        elif action == "eval":
            self.logic.press("=")
        elif action == "del":
            self.logic.press("DEL")

        self.gesture_status.set(f"Gesture: {action} {value or ''}")
        self._refresh_display()

    # ── Lifecycle ────────────────────────────
    def on_close(self):
        self.voice.stop()
        self.gesture.stop()
        self.destroy()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = SmartCalculatorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()