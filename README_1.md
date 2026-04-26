# Smart Multimodal Calculator
### Voice + Gesture + Button Input | Python + Tkinter

---

## Project Structure

```
smart_calculator/
├── main.py              ← Launch this file
├── calculator_logic.py  ← Math engine (expression builder + evaluator)
├── voice_handler.py     ← Microphone → SpeechRecognition → math expression
├── gesture_handler.py   ← Webcam → MediaPipe → finger/swipe → action
├── requirements.txt     ← All pip dependencies
└── README.md
```

---

## Setup & Installation

### Step 1 — Python version
Requires Python **3.9+**. Check with:
```bash
python --version
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```
> On Linux, also run: `sudo apt-get install portaudio19-dev`

### Step 3 — Run the app
```bash
python main.py
```

---

## How Each Mode Works

### ⌨ Basic Mode
- Click number/operator buttons to build an expression
- Press **=** to evaluate
- Press **C** to clear, **⌫** to delete last character
- History panel on the right — click any entry to reuse

### 🎤 Voice Mode
Switch to the Voice tab and press **Start Listening**.

| Say | Action |
|-----|--------|
| "five plus eight" | 5+8 |
| "nine times seven" | 9*7 |
| "hundred divided by four" | 100/4 |
| "clear" | Clears display |
| "equals" | Evaluates |

Voice is processed by Google Speech-to-Text via the SpeechRecognition library.
> Requires an active internet connection.

### ✋ Gesture Mode
Switch to the Gesture tab and press **Start Gesture Mode**.
Hold your hand clearly in front of the webcam.

| Gesture | Action |
|---------|--------|
| ☝ 1 finger | Input digit 1 |
| ✌ 2 fingers | Input digit 2 |
| 🤟 3 fingers | Input digit 3 |
| 🖖 4 fingers | Input digit 4 |
| 🖐 5 fingers (open palm) | Equals (=) |
| 👉 Swipe right | Cycle operator (+, −, ×, ÷) |
| 👈 Swipe left | Backspace |

There is a **1.2-second cooldown** between gesture actions to prevent accidental repeats.

---

## Architecture Diagram

```
┌────────────────────────────────────────────────┐
│               SmartCalculatorApp               │
│                  (main.py)                     │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  Basic   │  │  Voice   │  │   Gesture   │  │
│  │  Panel   │  │  Panel   │  │    Panel    │  │
│  └────┬─────┘  └────┬─────┘  └──────┬──────┘  │
│       │             │               │          │
│       ▼             ▼               ▼          │
│  ┌──────────────────────────────────────────┐  │
│  │           CalculatorLogic               │  │
│  │   expression builder + safe eval()      │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  VoiceHandler          GestureHandler          │
│  (background thread)   (background thread)     │
│  SpeechRecognition     OpenCV + MediaPipe       │
└────────────────────────────────────────────────┘
```

---

## Extending the Project

| Feature | Where to add |
|---------|-------------|
| Square root / power | `calculator_logic.py` → `press()` |
| Offline STT (Whisper) | `voice_handler.py` → swap `recognize_google()` |
| More gesture types | `gesture_handler.py` → `_capture_loop()` |
| Sound effects | `main.py` → import `playsound` |
| Save history to file | `calculator_logic.py` → write `self.history` to JSON |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `pyaudio` install fails | `pip install pipwin && pipwin install pyaudio` (Windows) |
| No microphone detected | Check OS permissions & default audio device |
| Webcam not opening | Try `cv2.VideoCapture(1)` in gesture_handler.py |
| MediaPipe import error | `pip install --upgrade mediapipe` |
| Voice not recognised | Check internet connection; Google STT needs it |
