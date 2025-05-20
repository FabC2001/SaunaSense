## This is the third test. It updates every 0.5s, but reads from sensors every 5s

## Changed how warning mode works
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

# === I2C Bus Setup ===
i2c = busio.I2C(board.SCL, board.SDA)

# === Sensor Initialization ===
sensor = adafruit_ahtx0.AHTx0(i2c)           # Temperature and humidity
apds = APDS9960(i2c)                         # Light sensor (APDS9960)
apds.enable_color = True                     # Enable color readings

# === Rotary Encoder Setup (Seesaw I2C) ===
encoder = Seesaw(i2c, addr=0x36)
rotary = rotaryio.IncrementalEncoder(encoder)
last_position = rotary.position              # Store initial encoder position
encoder.pin_mode(24, encoder.INPUT_PULLUP)   # Enable built-in encoder button
last_encoder_button = True                   # Previous state of encoder button

# === Display Setup (HT16K33) ===
display = Seg14x4(i2c)
display.fill(0)

# === LED Setup ===
green_led = digitalio.DigitalInOut(board.A2)
green_led.direction = digitalio.Direction.OUTPUT
yellow_led = digitalio.DigitalInOut(board.A3)
yellow_led.direction = digitalio.Direction.OUTPUT
red_led = digitalio.DigitalInOut(board.TX)
red_led.direction = digitalio.Direction.OUTPUT

# === Buzzer Setup (PWM-controlled passive buzzer) ===
buzzer = pwmio.PWMOut(board.A1, frequency=400, duty_cycle=0)

# === Stopwatch Button (External button on A0) ===
button = digitalio.DigitalInOut(board.A0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Configuration Parameters ===
target_temp = 80           # Initial preferred temperature (adjustable via encoder)
critical_temp = 95         # Absolute upper threshold for "danger"
STATE_SAFE = 0
STATE_WARNING = 1
STATE_DANGEROUS = 2
current_state = STATE_SAFE

# === Stopwatch State ===
stopwatch_running = False
stopwatch_start_time = 0
stopwatch_elapsed = 0
last_button_state = True   # For debounce logic

# === Display Mode State ===
display_mode = 0           # 0=temp, 1=humidity, 2=stopwatch, 3=set temp

# === Helper Functions ===

def get_ambient_light():
    """Returns ambient light level based on green channel."""
    try:
        _, g, _, _ = apds.color_data
        return g
    except Exception:
        return 100  # Fallback value in case of read failure

def set_display_brightness(ambient):
    """
    Adjusts display brightness based on ambient light.
    Maps green channel (0–300) to display brightness (0.1–1.0).
    """
    clamped = min(max(ambient, 0), 300)
    normalized = clamped / 300
    display.brightness = 0.1 + (normalized * 0.9)

def update_leds(current_temp):
    """
    Sets LED color based on how close the current temperature is to the target.
    Green = optimal range (±3°C)
    Yellow = within ±10°C
    Red = further than ±10°C
    """
    diff = abs(current_temp - target_temp)
    green_led.value = yellow_led.value = red_led.value = False
    if diff <= 3:
        green_led.value = True
    elif diff <= 10:
        yellow_led.value = True
    else:
        red_led.value = True

def determine_state(temp):
    """
    Returns one of the defined system states:
    - SAFE: within tolerance
    - WARNING: more than 10°C above target
    - DANGEROUS: above critical threshold
    """
    if temp >= critical_temp:
        return STATE_DANGEROUS
    elif temp - target_temp > 10:
        return STATE_WARNING
    else:
        return STATE_SAFE

def handle_state(state):
    """
    Controls the buzzer based on system state.
    Sounds briefly in both WARNING and DANGEROUS states.
    """
    if state == STATE_DANGEROUS or state == STATE_WARNING:
        buzzer.duty_cycle = 3000
        time.sleep(0.1)
        buzzer.duty_cycle = 0
    else:
        buzzer.duty_cycle = 0

def format_seconds(seconds):
    """Formats a time in seconds as MMSS for the stopwatch display."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:>2}{secs:02}"

# === Main Loop Timers ===
last_sensor_time = 0       # Last time sensor values were read
last_display_time = 0      # Last time LEDs and display were updated
sensor_interval = 5.0      # Seconds between sensor reads
update_interval = 0.5      # Seconds between LED/display updates

while True:
    now = time.monotonic()

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

    # --- Rotary Encoder Movement ---
    position = rotary.position
    if position != last_position:
        delta = position - last_position
        target_temp += delta
        target_temp = max(0, min(100, target_temp))
        last_position = position

    # --- Rotary Encoder Button Press ---
    encoder_button = encoder.digital_read(24)
    if last_encoder_button and not encoder_button:
        display_mode = (display_mode + 1) % 4
    last_encoder_button = encoder_button

    # === Sensor Readings every 5 seconds ===
    if now - last_sensor_time >= sensor_interval:
        last_sensor_time = now

        # Read all sensors
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
        ambient = get_ambient_light()

        # Apply brightness based on ambient light
        set_display_brightness(ambient)

        # Determine system state
        new_state = determine_state(temperature)
        if new_state != current_state:
            current_state = new_state
        handle_state(current_state)

    # === LED and Display Update every 0.5 seconds ===
    if now - last_display_time >= update_interval:
        last_display_time = now

        # Update LED color based on latest temperature
        update_leds(temperature)

        # Update display based on mode
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
            display.print(f"S{int(target_temp):>3}")

    time.sleep(0.05)  # Responsive button & encoder polling