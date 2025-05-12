import time
import board
import busio
import digitalio
import pwmio  # ✅ NEW for buzzer
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
apds.enable_color = True

# === Rotary Encoder (Seesaw) ===
encoder = Seesaw(i2c, addr=0x36)
rotary = rotaryio.IncrementalEncoder(encoder)
last_position = rotary.position

# === Display ===
display = Seg14x4(i2c)
display.brightness = 1.0
display.fill(0)

# === LEDs ===
green_led = digitalio.DigitalInOut(board.A2)
green_led.direction = digitalio.Direction.OUTPUT
yellow_led = digitalio.DigitalInOut(board.A3)
yellow_led.direction = digitalio.Direction.OUTPUT
red_led = digitalio.DigitalInOut(board.TX)
red_led.direction = digitalio.Direction.OUTPUT

# === Buzzer (PWM) ===
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)

# === Button (Stopwatch Control) ===
button = digitalio.DigitalInOut(board.A0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Configuration ===
target_temp = 80
critical_temp = 95
switch_interval = 5
STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE
last_switch = time.monotonic()
show_temperature = True
stopwatch_running = False
stopwatch_start_time = 0
stopwatch_elapsed = 0
last_button_state = True

# === Functions ===
def get_ambient_light():
    try:
        _, g, _, _ = apds.color_data
        return g
    except Exception:
        return 100

def update_leds(current_temp, ambient_light):
    diff = abs(current_temp - target_temp)
    bright = ambient_light < 100
    green_led.value = yellow_led.value = red_led.value = False
    if not bright:
        return
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
        buzzer.duty_cycle = 3000
        time.sleep(0.1)
        buzzer.duty_cycle = 0
    else:
        buzzer.duty_cycle = 0

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
    ambient = get_ambient_light()

    # === Display brightness based on ambient light ===
    if ambient < 50:
        display.brightness = 1.0
    elif ambient < 150:
        display.brightness = 0.5
    else:
        display.brightness = 0.1

    # === Update rotary encoder → target temperature ===
    position = rotary.position
    if position != last_position:
        delta = position - last_position
        target_temp += delta
        target_temp = max(40, min(110, target_temp))
        last_position = position

    # === Temperature state handling ===
    new_state = determine_state(temperature)
    if new_state != current_state:
        current_state = new_state
    handle_state(current_state)

    # === LED feedback ===
    update_leds(temperature, ambient)

    # === Stopwatch control via button ===
    current_button = button.value
    if last_button_state and not current_button:
        if stopwatch_running:
            stopwatch_elapsed += now - stopwatch_start_time
            stopwatch_running = False
        else:
            stopwatch_start_time = now
            stopwatch_running = True
    last_button_state = current_button

    # === Toggle display mode ===
    if now - last_switch >= switch_interval:
        show_temperature = not show_temperature
        last_switch = now

    # === Display output ===
    if show_temperature:
        display.print(f"T{int(temperature):>3}")
    elif stopwatch_running:
        elapsed = stopwatch_elapsed + (now - stopwatch_start_time)
        display.print(format_seconds(elapsed))
    else:
        display.print(f"H{int(humidity):>3}")

    time.sleep(0.1)