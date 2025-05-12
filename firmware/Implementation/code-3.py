import time
import board
import busio
import adafruit_ahtx0
from adafruit_ht16k33.segments import Seg14x4

# Set up I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Set up the AHT20 sensor
sensor = adafruit_ahtx0.AHTx0(i2c)

# Set up the 14-segment display
display = Seg14x4(i2c)
display.brightness = 1.0
display.fill(0)  # Clear display

# Track which mode is being shown
show_temperature = True
last_switch = time.monotonic()

while True:
    now = time.monotonic()

    # Read values from the sensor
    temperature = sensor.temperature  # °C
    humidity = sensor.relative_humidity  # %

    # Every 5 seconds, switch display mode
    if now - last_switch >= 5:
        show_temperature = not show_temperature
        last_switch = now

    # Format and display the selected value
    if show_temperature:
        display_text = f"T{temperature:>4.0f}"  # e.g. T  23
    else:
        display_text = f"H{humidity:>4.0f}"      # e.g. H  47

    display.print(display_text)
    time.sleep(0.1)