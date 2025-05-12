import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import rotaryio, digitalio

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c, addr=0x36)

# Set up encoder and button
encoder = rotaryio.IncrementalEncoder(ss)
button = digitalio.DigitalIO(ss, 24)

last_position = None

while True:
    pos = encoder.position
    if pos != last_position:
        print("Position:", pos)
        last_position = pos

    if not button.value:
        print("Button pressed!")

    time.sleep(0.1)