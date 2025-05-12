import time
import board
import busio
import digitalio
import pwmio  # ✅ Added for PWM buzzer
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
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)  # ✅ 400 Hz, initially off

# === Configuration ===
target_temp = 80  # user-defined safe temp
critical_temp = 95  # buzzer alert threshold
switch_interval = 5  # seconds for display switch

# === State Machine States ===
STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE

last_switch = time.monotonic()
show_temperature = True

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
    if state == STATE_SAFE or state == STATE_WARNING:
        buzzer.duty_cycle = 0  # Off
    elif state == STATE_DANGEROUS:
        # Pulse the buzzer briefly
        buzzer.duty_cycle = 3000  # ✅ Max duty cycle
        time.sleep(0.1)
        buzzer.duty_cycle = 0

while True:
    now = time.monotonic()

    temperature = sensor.temperature
    humidity = sensor.relative_humidity

    # Update state
    new_state = determine_state(temperature)
    if new_state != current_state:
        current_state = new_state

    # Act based on state
    handle_state(current_state)

    # Update LEDs and display
    update_leds(temperature)

    if now - last_switch >= switch_interval:
        show_temperature = not show_temperature
        last_switch = now

    if show_temperature:
        display.print(f"T{int(temperature):>3}")
    else:
        display.print(f"H{int(humidity):>3}")

    time.sleep(0.2)