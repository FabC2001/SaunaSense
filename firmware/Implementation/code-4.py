import time
import board
import busio
import adafruit_ahtx0
from adafruit_ht16k33.segments import Seg14x4
import digitalio

# === Setup I2C for both display and sensors ===
i2c = busio.I2C(board.SCL, board.SDA)

# === Sensor Setup: AHT20 for temp & humidity ===
sensor = adafruit_ahtx0.AHTx0(i2c)

# === Display Setup: HT16K33 14-segment ===
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

# === Config ===
switch_interval = 5  # seconds between switching display modes
last_switch = time.monotonic()
show_temperature = True

# Simulated target temperature (replace with potentiometer later)
target_temp = 80  # Celsius

def update_leds(current_temp, target_temp):
    diff = abs(current_temp - target_temp)

    # Turn all LEDs off
    green_led.value = False
    yellow_led.value = False
    red_led.value = False

    # Choose LED based on closeness
    if diff <= 3:
        green_led.value = True
    elif diff <= 10:
        yellow_led.value = True
    else:
        red_led.value = True

while True:
    now = time.monotonic()

    # Read from AHT20
    temperature = sensor.temperature  # °C
    humidity = sensor.relative_humidity  # %

    # Update LEDs
    update_leds(temperature, target_temp)

    # Switch display mode every 5 seconds
    if now - last_switch >= switch_interval:
        show_temperature = not show_temperature
        last_switch = now

    # Show temperature or humidity on display
    if show_temperature:
        display_text = f"T{int(temperature):>3}"
    else:
        display_text = f"H{int(humidity):>3}"

    display.print(display_text)

    time.sleep(0.2)