import time
import board
import busio
import adafruit_apds9960.apds9960

# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
try:
    apds = adafruit_apds9960.apds9960.APDS9960(i2c)
    print("APDS-9960 sensor initialized successfully.")
except Exception as e:
    print(f"Error initializing sensor: {e}")
    exit()

apds.enable_proximity = True
apds.enable_light = True  # Enable ambient light sensing
apds.enable_color = True
apds.enable_gesture = True

# resten på https://www.w3schools.com/colors/colors_rgb.asp