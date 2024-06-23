# LED Test am Adafruit MCP23017

import time
import sys
from gpiozero import Button
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

# ----------------
# Taster
# ----------------

# Parterre
Tast_PA_auto = mcp0.get_pin(12)
Tast_PA_auto.direction = digitalio.Direction.INPUT
Tast_PA_auto.pull = digitalio.Pull.UP

Tast_PA_aus = mcp0.get_pin(13)
Tast_PA_aus.direction = digitalio.Direction.INPUT
Tast_PA_aus.pull = digitalio.Pull.UP

Tast_PA_hand = mcp0.get_pin(14)
Tast_PA_hand.direction = digitalio.Direction.INPUT
Tast_PA_hand.pull = digitalio.Pull.UP

# unteres Becken
Tast_UB_auto = mcp1.get_pin(0)
Tast_UB_auto.direction = digitalio.Direction.INPUT
Tast_UB_auto.pull = digitalio.Pull.UP

Tast_UB_aus = mcp1.get_pin(1)
Tast_UB_aus.direction = digitalio.Direction.INPUT
Tast_UB_aus.pull = digitalio.Pull.UP

Tast_UB_hand = mcp1.get_pin(2)
Tast_UB_hand.direction = digitalio.Direction.INPUT
Tast_UB_hand.pull = digitalio.Pull.UP

# oberes Becken
Tast_OB_auto = mcp1.get_pin(3)
Tast_OB_auto.direction = digitalio.Direction.INPUT
Tast_OB_auto.pull = digitalio.Pull.UP

Tast_OB_aus = mcp1.get_pin(4)
Tast_OB_aus.direction = digitalio.Direction.INPUT
Tast_OB_aus.pull = digitalio.Pull.UP

Tast_OB_hand = mcp1.get_pin(5)
Tast_OB_hand.direction = digitalio.Direction.INPUT
Tast_OB_hand.pull = digitalio.Pull.UP


# Taster Test
# MCP0: Pin 12, 13, 14 aktivieren
mcp0.interrupt_enable = (1 << 12) | (1 << 13) | (1 << 14)

# MCP1: Pin 0, 1, 2, 3, 4, 5 aktivieren
mcp1.interrupt_enable = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)

# Interrupt Behandlung konfigurieren
# Reaktion auf alle Changes
mcp0.interrupt_configuration = 0x0000
mcp1.interrupt_configuration = 0x0000
# Interrupt as open drain and mirrored
mcp0.io_control = 0x44  
mcp1.io_control = 0x44  

# Reaktion nur auf Drücken
#mcp0.interrupt_configuration = 0xFFFF
#mcp0.default_value = 0xFFFF
#mcp1.interrupt_configuration = 0xFFFF
#mcp1.default_value = 0xFFFF

# Interrupt as open drain and mirrored
#mcp0.io_control = 0x44  
#mcp1.io_control = 0x44  

# Löschen aller Interrupts
mcp0.clear_ints() 
mcp1.clear_ints() 

def extract_gpio_number(port):
	# Konvertiere 'port' in einen String, falls es keiner ist
	port_str = str(port)
	
	# Beispiel: port_str ist ein String wie "<gpiozero.Button object on pin GPIO22, pull_up=True, is_active=True>"
	# Wir wollen nur die GPIO-Nummer (z.B. "GPIO22") extrahieren
	start_index = port_str.find("GPIO")
	if start_index != -1:
		end_index = port_str.find(",", start_index)
		if end_index != -1:
			return port_str[start_index:end_index]
		else:
			return port_str[start_index:]
	return None
	
def interrupt_handler_pressed(port):
	print("\n")
	gpio_number = extract_gpio_number(port)
	print("Interrupt Handler an RPi Pin ",gpio_number, " für ", mcp0.int_flag, mcp1.int_flag)
	"""Callback function to be called when an Interrupt occurs."""
	for pin_flag in mcp0.int_flag:
		print("MCP0 Interrupt connected to Pin: {}".format(gpio_number))
		print("MCP0 Pin number: {} changed to: ".format(pin_flag))
	for pin_flag in mcp1.int_flag:
		print("MCP1 Interrupt connected to Pin: {}".format(gpio_number))
		print("MCP1 Pin number: {} changed to: ".format(pin_flag))
	mcp0.clear_ints() 
	mcp1.clear_ints() 
	print("cleared")


def interrupt_handler_released(port):
	led_PA_active.value=True
	mcp0.clear_ints()
	mcp1.clear_ints()
	time.sleep(0.2)
	led_PA_active.value=False
	mcp0.clear_ints() 
	mcp1.clear_ints() 

# RPi GPIO als Interrupt Pins konfigurieren
mcp0irAPin = 22
mcp0irA = Button(mcp0irAPin, pull_up=True, bounce_time=0.1)
mcp0irA.when_pressed = interrupt_handler_pressed
#mcp0irA.when_released = None

mcp0irBPin = 23
mcp0irB = Button(mcp0irBPin, pull_up=True, bounce_time=0.1)
mcp0irB.when_pressed = interrupt_handler_pressed
#mcp0irB.when_released = None

mcp1irAPin = 24
mcp1irA = Button(mcp1irAPin, pull_up=True, bounce_time=0.1)
mcp1irA.when_pressed = interrupt_handler_pressed
#mcp1irA.when_released = None

mcp1irBPin = 25
mcp1irB = Button(mcp1irBPin, pull_up=True, bounce_time=0.1)
mcp1irB.when_pressed = interrupt_handler_pressed
#mcp1irB.when_released = None


try:
	print("When button is pressed you'll see a message")
	while True:
		# Hier könnte deine Hauptfunktionalität der Schleife stehen.
		time.sleep(0.1)
		print(".", end='', flush=True)
		pass
except KeyboardInterrupt:
	print("\nExiting the loop due to KeyboardInterrupt.")
	exit(1)