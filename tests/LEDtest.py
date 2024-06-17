# LED Test am Adafruit MCP23017

import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017


# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create an instance of MCP23017 class 
mcp0 = MCP23017(i2c, address=0x20)
mcp1 = MCP23017(i2c, address=0x21)
#mcp2 = MCP23017(i2c, address=0x22)

# ---------------
# LED
# ---------------

# Parterre
led_PA_active = mcp0.get_pin(0)
led_PA_active.switch_to_output(value=False)

led_PA_auto = mcp0.get_pin(1)
led_PA_auto.switch_to_output(value=False)

led_PA_aus = mcp0.get_pin(2)
led_PA_aus.switch_to_output(value=False)

led_PA_hand = mcp0.get_pin(3)
led_PA_hand.switch_to_output(value=False)

# unteres Becken
led_UB_active = mcp0.get_pin(4)
led_UB_active.switch_to_output(value=False)

led_UB_auto = mcp0.get_pin(5)
led_UB_auto.switch_to_output(value=False)

led_UB_aus = mcp0.get_pin(6)
led_UB_aus.switch_to_output(value=False)

led_UB_hand = mcp0.get_pin(7)
led_UB_hand.switch_to_output(value=False)

# oberes Becken
led_OB_active = mcp0.get_pin(8)
led_OB_active.switch_to_output(value=False)

led_OB_auto = mcp0.get_pin(9)
led_OB_auto.switch_to_output(value=False)

led_OB_aus = mcp0.get_pin(10)
led_OB_aus.switch_to_output(value=False)

led_OB_hand = mcp0.get_pin(11)
led_OB_hand.switch_to_output(value=False)

# Fehler-LED
led_ERR_active = mcp0.get_pin(15)
led_ERR_active.switch_to_output(value=False)

# LED Test
led_PA_active.value = True
led_PA_auto.value = True
led_PA_aus.value = True
led_PA_hand.value = True

led_UB_active.value = True
led_UB_auto.value = True
led_UB_aus.value = True
led_UB_hand.value = True

led_OB_active.value = True
led_OB_auto.value = True
led_OB_aus.value = True
led_OB_hand.value = True

led_ERR_active.value=True

time.sleep(1)

led_PA_active.value = False
time.sleep(0.5)
led_PA_auto.value = False
time.sleep(0.5)
led_PA_aus.value = False
time.sleep(0.5)
led_PA_hand.value = False
time.sleep(0.5)

led_UB_active.value = False
time.sleep(0.5)
led_UB_auto.value = False
time.sleep(0.5)
led_UB_aus.value = False
time.sleep(0.5)
led_UB_hand.value = False
time.sleep(0.5)

led_OB_active.value = False
time.sleep(0.5)
led_OB_auto.value = False
time.sleep(0.5)
led_OB_aus.value = False
time.sleep(0.5)
led_OB_hand.value = False
time.sleep(0.5)

led_ERR_active.value=False

i = 0
while i<20:
	# Blink Error-LED
	led_ERR_active.value=True
	time.sleep(0.2)
	led_ERR_active.value=False
	time.sleep(0.2)
	i = i+1

led_ERR_active.value=False

exit(0)
