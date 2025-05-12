import time
import board
import analogio
import pwmio

# Set up potentiometer input
pot = analogio.AnalogIn(board.A3)

# Set up PWM output to LED
led = pwmio.PWMOut(board.A0, frequency=5000, duty_cycle=0)

def read_pot():
    return pot.value  # 0–65535

while True:
    val = read_pot()
    led.duty_cycle = val  # Map pot value directly to brightness
    print("Potentiometer:", val)
    time.sleep(0.05)