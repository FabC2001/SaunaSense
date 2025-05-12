import time
import board
import digitalio
import analogio
import pwmio
import adafruit_ahtx0
import adafruit_apds9960.apds9960
import adafruit_ht16k33.segments

from adafruit_apds9960.apds9960 import APDS9960
from adafruit_ht16k33.segments import BigSegment

# === I2C setup ===
i2c = board.I2C()
aht20 = adafruit_ahtx0.AHTx0(i2c)
apds = adafruit_apds9960.apds9960.APDS9960(i2c)
apds.enable_light_sensor = True
display = BigSegment(i2c)

# === Display Setup ===
display.fill(0)

# === GPIO setup ===
button = digitalio.DigitalInOut(board.D5)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

led = digitalio.DigitalInOut(board.D6)
led.direction = digitalio.Direction.OUTPUT

buzzer = pwmio.PWMOut(board.D9, duty_cycle=0, frequency=440, variable_frequency=True)

# === Potentiometer ===
pot = analogio.AnalogIn(board.A0)
def get_target_temp():
    return 40 + ((pot.value / 65535) * 60)  # Range: 40–100°C

# === Stopwatch ===
start_time = None

# === Display Modes ===
modes = ["TEMP", "HUMI", "TIME"]
current_mode = 0
last_button_state = True
last_button_press_time = 0

# === Constants ===
CRITICAL_TEMP = 90  # Red blinking + buzzer
LED_TOLERANCES = [3, 10]  # Green: ±3, Yellow: ±10, Red: >10

# === Helper Functions ===
def update_led(temp, target):
    diff = abs(temp - target)
    if diff <= LED_TOLERANCES[0]:
        led.value = True  # Green (placeholder for multi-color)
    elif diff <= LED_TOLERANCES[1]:
        led.value = True  # Yellow (also true for now)
    else:
        led.value = True  # Red
    if temp > CRITICAL_TEMP:
        blink_led()
        sound_buzzer()

def blink_led():
    for _ in range(3):
        led.value = True
        time.sleep(0.2)
        led.value = False
        time.sleep(0.2)

def sound_buzzer():
    buzzer.duty_cycle = 32768  # 50%
    buzzer.frequency = 880
    time.sleep(1)
    buzzer.duty_cycle = 0

def read_button():
    global last_button_state, last_button_press_time, current_mode, start_time
    current_state = button.value
    now = time.monotonic()
    if last_button_state and not current_state:
        last_button_press_time = now
    elif not last_button_state and current_state:
        press_duration = now - last_button_press_time
        if press_duration > 1:
            # Long press: reset stopwatch
            start_time = time.monotonic()
        else:
            # Short press: change mode
            current_mode = (current_mode + 1) % len(modes)
    last_button_state = current_state

def update_display(mode, temp, humi, elapsed):
    if mode == "TEMP":
        display.print(f"{temp:4.0f}")
    elif mode == "HUMI":
        display.print(f"{humi:4.0f}")
    elif mode == "TIME":
        display.print(f"{int(elapsed):4d}")

def adjust_brightness():
    # Brightness from ambient light: 0–255
    brightness = apds.ambient_light
    if brightness is not None:
        level = max(1, min(int(brightness / 100), 15))  # Clamp to 1–15
        display.brightness = level

# === Main Loop ===
start_time = time.monotonic()
while True:
    adjust_brightness()
    read_button()

    temp = aht20.temperature
    humi = aht20.relative_humidity
    target_temp = get_target_temp()
    elapsed = time.monotonic() - start_time

    update_led(temp, target_temp)
    update_display(modes[current_mode], temp, humi, elapsed)

    time.sleep(0.5)
