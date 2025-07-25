import time
import board
import busio
import digitalio
import pwmio
import adafruit_ahtx0
from adafruit_ht16k33.segments import Seg14x4
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw.seesaw import Seesaw
import adafruit_seesaw.rotaryio as rotaryio

# === I2C Setup ===
i2c = busio.I2C(board.SCL, board.SDA)

# === Sensors ===
sensor = adafruit_ahtx0.AHTx0(i2c)
apds = APDS9960(i2c)
apds.enable_color = True  # Use green channel for ambient light

# === Rotary Encoder Setup (Seesaw I2C) ===
encoder = Seesaw(i2c, addr=0x36)
rotary = rotaryio.IncrementalEncoder(encoder)
last_position = rotary.position

# === Display Setup ===
display = Seg14x4(i2c)
display.fill(0)

# === LEDs Setup ===
green_led = digitalio.DigitalInOut(board.A2)
green_led.direction = digitalio.Direction.OUTPUT
yellow_led = digitalio.DigitalInOut(board.A3)
yellow_led.direction = digitalio.Direction.OUTPUT
red_led = digitalio.DigitalInOut(board.TX)
red_led.direction = digitalio.Direction.OUTPUT

# === Buzzer Setup (PWM) ===
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)

# === Button Setup (Stopwatch Toggle) ===
button = digitalio.DigitalInOut(board.A0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Config ===
target_temp = 80
critical_temp = 95
STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE

# === Stopwatch Variables ===
stopwatch_running = False
stopwatch_start_time = 0
stopwatch_elapsed = 0
last_button_state = True

# === Display Mode Rotation ===
display_mode = 0  # 0 = Temp, 1 = Humidity, 2 = Stopwatch, 3 = Set Temp
last_switch = time.monotonic()
switch_interval = 3  # seconds

# === Functions ===

def get_ambient_light():
    """Return green channel value from APDS9960."""
    try:
        _, g, _, _ = apds.color_data
        return g
    except Exception:
        return 100  # fallback value

def set_display_brightness(ambient):
    """Smoothly map ambient light (0–300) to display brightness (0.1–1.0)."""
    clamped = min(max(ambient, 0), 300)
    normalized = clamped / 300
    display.brightness = 0.1 + (normalized * 0.9)

def update_leds(current_temp):
    """Show green/yellow/red based on how close we are to target_temp."""
    diff = abs(current_temp - target_temp)
    green_led.value = yellow_led.value = red_led.value = False
    if diff <= 3:
        green_led.value = True
    elif diff <= 10:
        yellow_led.value = True
    else:
        red_led.value = True

def determine_state(temp):
    """Return system state: safe, warning, or dangerous."""
    if temp >= critical_temp:
        return STATE_DANGEROUS
    elif abs(temp - target_temp) > 10:
        return STATE_WARNING
    else:
        return STATE_SAFE

def handle_state(state):
    """Activate buzzer if temperature is dangerous."""
    if state == STATE_DANGEROUS:
        buzzer.duty_cycle = 3000
        time.sleep(0.1)
        buzzer.duty_cycle = 0
    else:
        buzzer.duty_cycle = 0

def format_seconds(seconds):
    """Format stopwatch seconds to MMSS display string."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:>2}{secs:02}"

# === Main Loop ===
while True:
    now = time.monotonic()

    # === Sensor Readings ===
    temperature = sensor.temperature
    humidity = sensor.relative_humidity
    ambient = get_ambient_light()

    # === Display Brightness ===
    set_display_brightness(ambient)

    # === Update target temperature from rotary encoder ===
    position = rotary.position
    if position != last_position:
        delta = position - last_position
        target_temp += delta
        target_temp = max(40, min(110, target_temp))
        last_position = position

    # === Update system state and handle buzzer ===
    new_state = determine_state(temperature)
    if new_state != current_state:
        current_state = new_state
    handle_state(current_state)

    # === LED Feedback ===
    update_leds(temperature)

    # === Stopwatch Button Logic ===
    current_button = button.value
    if last_button_state and not current_button:
        if stopwatch_running:
            stopwatch_elapsed += now - stopwatch_start_time
            stopwatch_running = False
        else:
            stopwatch_start_time = now
            stopwatch_running = True
    last_button_state = current_button

    # === Display Mode Switching ===
    if now - last_switch >= switch_interval:
        display_mode = (display_mode + 1) % 4  # 0–3
        last_switch = now

    # === Display Output ===
    if display_mode == 0:
        display.print(f"T{int(temperature):>3}")
    elif display_mode == 1:
        display.print(f"H{int(humidity):>3}")
    elif display_mode == 2:
        if stopwatch_running:
            elapsed = stopwatch_elapsed + (now - stopwatch_start_time)
        else:
            elapsed = stopwatch_elapsed
        display.print(format_seconds(elapsed))
    elif display_mode == 3:
        display.print(f"S{int(target_temp):>3}")  # Show set temp

    time.sleep(0.1)