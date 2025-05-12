import time
import board
import busio
import digitalio
import pwmio
import adafruit_ahtx0
from adafruit_ht16k33.segments import Seg14x4

# === Setup I2C for display and sensors ===
i2c = busio.I2C(board.SCL, board.SDA)

# === Sensor Setup ===
sensor = adafruit_ahtx0.AHTx0(i2c)

# === Display Setup ===
display = Seg14x4(i2c)
display.brightness = 1.0
display.fill(0)

# === LED Setup ===
green_led = digitalio.DigitalInOut(board.A2)
green_led.direction = digitalio.Direction.OUTPUT

yellow_led = digitalio.DigitalInOut(board.A3)
yellow_led.direction = digitalio.Direction.OUTPUT

red_led = digitalio.DigitalInOut(board.TX)
red_led.direction = digitalio.Direction.OUTPUT

# === Buzzer Setup (PWM) ===
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)

# === Button Setup (start/stop stopwatch) ===
button = digitalio.DigitalInOut(board.A0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Configuration ===
target_temp = 80
critical_temp = 95
switch_interval = 5  # seconds between display modes

STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE

# === Timing & Display Mode ===
last_switch = time.monotonic()
display_mode = 0  # 0 = temp, 1 = humidity, 2 = stopwatch

# === Stopwatch variables ===
stopwatch_running = False
stopwatch_start_time = 0
stopwatch_elapsed = 0
last_button_state = True

# === Functions ===

def update_leds(current_temp):
    diff = abs(current_temp - target_temp)
    green_led.value = False
    yellow_led.value = False
    red_led.value = False
    if diff <= 3:
        green_led.value = True
    elif diff <= 10:
        yellow_led.value = True
    else:
        red_led.value = True

def determine_state(temp):
    if temp >= critical_temp:
        return STATE_DANGEROUS
    elif abs(temp - target_temp) > 10:
        return STATE_WARNING
    else:
        return STATE_SAFE

def handle_state(state):
    if state == STATE_DANGEROUS:
        buzzer.duty_cycle = 3000  # Beep
        time.sleep(0.1)
        buzzer.duty_cycle = 0
    else:
        buzzer.duty_cycle = 0  # Always off otherwise

def format_seconds(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:>2}{secs:02}"

# === Main Loop ===

while True:
    now = time.monotonic()

    # === Read sensors ===
    temperature = sensor.temperature
    humidity = sensor.relative_humidity

    # === State machine for temperature ===
    new_state = determine_state(temperature)
    if new_state != current_state:
        current_state = new_state
    handle_state(current_state)

    # === LED Feedback ===
    update_leds(temperature)

    # === Button debounce for stopwatch control ===
    current_button = button.value
    if last_button_state and not current_button:  # Button just pressed
        if stopwatch_running:
            stopwatch_elapsed += now - stopwatch_start_time
            stopwatch_running = False
        else:
            stopwatch_start_time = now
            stopwatch_running = True
    last_button_state = current_button

    # === Cycle display mode every switch_interval seconds ===
    if now - last_switch >= switch_interval:
        display_mode = (display_mode + 1) % 3  # 0 → 1 → 2 → 0 ...
        last_switch = now

    # === Display output ===
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

    time.sleep(0.1)