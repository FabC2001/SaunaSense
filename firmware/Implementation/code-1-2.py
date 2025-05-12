import time
import board
import busio
import adafruit_ahtx0

# Set up I2C bus using QT Py's SCL and SDA
i2c = busio.I2C(board.SCL, board.SDA)

# Create the AHT20 sensor object
sensor = adafruit_ahtx0.AHTx0(i2c)

# Loop to print temperature and humidity
while True:
    temperature = sensor.temperature  # in Celsius
    humidity = sensor.relative_humidity  # in %
    
    print(f"Temperature: {temperature:.1f} °C")
    print(f"Humidity: {humidity:.1f} %")
    print("--------------------------")
    
    time.sleep(2)  # Wait 2 seconds between readings