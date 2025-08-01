import time
import board
import busio
import digitalio
import pwmio
import adafruit_ahtx0
from adafruit_ht16k33.segments import Seg14x4
from adafruit_apds9960.apds9960 import APDS9960

# === I2C Setup ===
i2c = busio.I2C(board.SCL, board.SDA)

# === Sensors ===
sensor = adafruit_ahtx0.AHTx0(i2c)
apds = APDS9960(i2c)
apds.enable_color = True  # Enable color sensor (used for ambient light)

# === Display Setup (14-segment alphanumeric) ===
display = Seg14x4(i2c)
display.fill(0)

# === LED Setup (Always visible based on temperature) ===
green_led = digitalio.DigitalInOut(board.A2)
green_led.direction = digitalio.Direction.OUTPUT

yellow_led = digitalio.DigitalInOut(board.A3)
yellow_led.direction = digitalio.Direction.OUTPUT

red_led = digitalio.DigitalInOut(board.TX)
red_led.direction = digitalio.Direction.OUTPUT

# === Buzzer Setup (PWM for passive buzzer) ===
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)

# === Button Setup (for stopwatch toggle) ===
button = digitalio.DigitalInOut(board.A0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Configuration Parameters ===
target_temp = 80               # User's preferred temp (°C)
critical_temp = 95             # Temperature considered dangerous (°C)
switch_interval = 5            # Seconds between display mode switches

# === State Machine Definitions ===
STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE

# === Stopwatch Variables ===
stopwatch_running = False
stopwatch_start_time = 0
stopwatch_elapsed = 0
last_button_state = True

# === Display Timing ===
last_switch = time.monotonic()
show_temperature = True  # Toggle between temp and humidity/stopwatch

# === Helper Functions ===

def get_ambient_light():
    """Returns ambient light level from APDS9960 (green channel)."""
    try:
        _, g, _, _ = apds.color_data
        return g
    except Exception:
        return 100  # Fallback value

def set_display_brightness(ambient):
    """Smoothly adjusts display brightness based on ambient light."""
    clamped = min(max(ambient, 0), 300)         # Clamp to 0–300
    normalized = clamped / 300                  # 0.0–1.0 scale
    display.brightness = 0.1 + (normalized * 0.9)  # Map to 0.1–1.0

def update_leds(current_temp):
    """Lights up the appropriate LED based on proximity to target temp."""
    diff = abs(current_temp - target_temp)
    green_led.value = yellow_led.value = red_led.value = False

    if diff <= 3:
        green_led.value = True
    elif diff <= 10:
        yellow_led.value = True
    else:
        red_led.value = True

def determine_state(temp):
    """Returns current system state based on temperature."""
    if temp >= critical_temp:
        return STATE_DANGEROUS
    elif abs(temp - target_temp) > 10:
        return STATE_WARNING
    else:
        return STATE_SAFE

def handle_state(state):
    """Activates buzzer if in dangerous state."""
    if state == STATE_DANGEROUS:
        buzzer.duty_cycle = 3000
        time.sleep(0.1)
        buzzer.duty_cycle = 0
    else:
        buzzer.duty_cycle = 0

def format_seconds(seconds):
    """Formats seconds as MMSS string (e.g., 02:35)."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:>2}{secs:02}"

# === Main Loop ===
while True:
    now = time.monotonic()

    # --- Sensor Readings ---
    temperature = sensor.temperature
    humidity = sensor.relative_humidity
    ambient = get_ambient_light()

    # --- Adjust Display Brightness ---
    set_display_brightness(ambient)

    # --- Update System State ---
    new_state = determine_state(temperature)
    if new_state != current_state:
        current_state = new_state
    handle_state(current_state)

    # --- LED Feedback ---
    update_leds(temperature)

    # --- Stopwatch Button Handling ---
    current_button = button.value
    if last_button_state and not current_button:
        if stopwatch_running:
            stopwatch_elapsed += now - stopwatch_start_time
            stopwatch_running = False
        else:
            stopwatch_start_time = now
            stopwatch_running = True
    last_button_state = current_button

    # --- Display Mode Toggle ---
    if now - last_switch >= switch_interval:
        show_temperature = not show_temperature
        last_switch = now

    # --- Display Output ---
    if show_temperature:
        display.print(f"T{int(temperature):>3}")
    elif stopwatch_running:
        elapsed = stopwatch_elapsed + (now - stopwatch_start_time)
        display.print(format_seconds(elapsed))
    else:
        display.print(f"H{int(humidity):>3}")

    time.sleep(0.1)