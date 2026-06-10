For a README, I'd recommend a more professional and open-source-friendly version like this:

# Lumberjack Bot

## 1. Overview

`lumberjack-bot` is a Python automation script designed to play Telegram's **Lumberjack** game automatically.

Due to browser security restrictions such as **CORS**, protected **iframes**, and **Canvas isolation**, the bot does not interact with the game's internal code. Instead, it operates at the **operating system and hardware level** by:

* Capturing and analyzing screen pixels.
* Detecting tree branches by inspecting colors on the left and right sides of the trunk.
* Determining the safest side for the hero to move.
* Simulating mouse clicks to perform chops.
* Counting successful chops in real time.
* Automatically stopping when the configured target score is reached.

### Why this approach?

The game runs inside a protected browser environment, making direct code interaction impossible. Operating-system-level screen analysis and mouse simulation provide a universal solution that works regardless of browser implementation.

This project is intended **for educational purposes only**, demonstrating concepts such as:

* Computer Vision
* State Machines
* Input Automation
* Decision-Making Logic

---

## 2. Requirements & Installation

### 1. Install Python

Python **3.8 or newer** is required.

Check your version:

```bash
python --version
```

### 2. Download the Project

Clone or download the repository and navigate to the project directory.

### 3. Install Runtime Dependencies

Required packages:

```bash
pip install Pillow pyautogui keyboard
```

Alternatively, OpenCV can be used instead of Pillow:

```bash
pip install opencv-python pyautogui keyboard
```

### 4. Platform Notes

#### Keyboard Permissions

The `keyboard` library typically requires elevated privileges to monitor global key presses.

**Windows**

Run your terminal as **Administrator**.

**Linux/macOS**

Launch the script with:

```bash
sudo python lumberjack_bot_main.py
```

#### Linux Notes

* `pyautogui` works best under **X11**.
* Additional packages such as `python3-tk` and `scrot` may be required.
* Full functionality may not be available under **Wayland**.
* The `keyboard` library cannot capture global keys without root privileges.

---

## 3. Configuration

All user-configurable settings are located at the top of `lumberjack_bot_main.py` inside the:

```python
# USER CONFIGURABLE VARIABLES
```

section.

### TARGET_SCORE

The score at which the bot automatically stops.

Valid range:

```python
1 - 1,000,000
```

Example:

```python
TARGET_SCORE = 269
```

### TOLERANCE

Color matching tolerance (`0–255`).

Lower values provide stricter matching, while higher values allow more variation.

```python
TOLERANCE = 30
```

### BRANCH_COLOR

Expected RGB color of tree branches.

Adjust this value if your game uses different branch colors.

```python
BRANCH_COLOR = RGBColor(r=139, g=90, b=43)
```

### MIN_DELAY_MS / MAX_DELAY_MS

Randomized delay between consecutive chops.

Requirements:

```python
10 <= MIN_DELAY_MS <= MAX_DELAY_MS <= 5000
```

Example:

```python
MIN_DELAY_MS = 100
MAX_DELAY_MS = 400
```

### INITIAL_HERO_SIDE

Starting side of the hero.

```python
INITIAL_HERO_SIDE = Side.LEFT
```

or

```python
INITIAL_HERO_SIDE = Side.RIGHT
```

### USE_PRESET_COORDS

Controls how screen coordinates are obtained.

#### Interactive Calibration (Recommended)

```python
USE_PRESET_COORDS = False
```

#### Manual Coordinates

```python
USE_PRESET_COORDS = True
```

When enabled, the bot uses manually defined values for:

* `LEFT_POINT`
* `RIGHT_POINT`
* `TOP_POINT`

---

## 4. Calibration Guide

Calibration configures the screen coordinates used to inspect the tree and detect branches.

### 4a. Interactive Calibration (Recommended)

1. Ensure:

```python
USE_PRESET_COORDS = False
```

2. Open the Telegram Lumberjack game and make sure it is visible on screen.

3. Launch the bot:

```bash
python lumberjack_bot_main.py
```

4. The script will request the following points in order:

   1. Left branch detection point
   2. Right branch detection point
   3. Top reference point (canvas boundary)

5. Move your mouse to the requested position.

6. Press **Space** to confirm the coordinate.

7. If a coordinate is outside the screen bounds, the script will reject it and request a new value.

8. After all three points are confirmed, the coordinates are saved and the bot enters the **IDLE** state.

---

### 4b. Manual Coordinate Configuration

If you already know the required coordinates:

```python
USE_PRESET_COORDS = True

LEFT_POINT = Point(x=800, y=500)
RIGHT_POINT = Point(x=1120, y=500)
TOP_POINT = Point(x=960, y=200)
```

### Finding Pixel Coordinates

Run:

```bash
python -c "import pyautogui, time; time.sleep(3); print(pyautogui.position())"
```

Move your cursor to the desired location within 3 seconds.

The terminal will print:

```text
(x, y)
```

for the current mouse position.

---

## 5. Usage

Start the bot:

```bash
python lumberjack_bot_main.py
```

After dependency checks and calibration (if required), the bot enters the **IDLE** state.

### Controls

| Key | Action         |
| --- | -------------- |
| S   | Start chopping |
| Q   | Stop and exit  |

### Automatic Stop

The bot automatically terminates once:

```python
CURRENT_SCORE >= TARGET_SCORE
```

---

## 6. Safety Notes

### PyAutoGUI Fail-Safe

If the bot becomes unresponsive or behaves unexpectedly:

Move your mouse rapidly to **any corner of the screen**.

PyAutoGUI will immediately raise a:

```python
FailSafeException
```

and stop execution.

### Global Keyboard Hooks

The `keyboard` library captures global key events.

While the bot is running, the configured hotkeys (`S` and `Q`) may also affect other applications.

### Educational Use

This project is provided **for educational and research purposes only**.

The author does not encourage violating the terms of service of any third-party platform, application, or game.

---

## 7. Running Tests

The project includes both:

* Unit Tests
* Property-Based Tests

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run the Test Suite

```bash
pytest
```

### Run With Verbose Output

```bash
pytest -v
```

---

## Features

* OS-level pixel detection
* Automatic branch recognition
* Human-like randomized delays
* Interactive calibration mode
* Manual coordinate mode
* Target score auto-stop
* Global hotkey controls
* Cross-platform Python implementation
* Unit and property-based testing support
* Educational computer vision example
