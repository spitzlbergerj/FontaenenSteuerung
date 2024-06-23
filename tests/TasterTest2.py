import time
from gpiozero import Button
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create instances of MCP23017 class
mcp0 = MCP23017(i2c, address=0x20)
mcp1 = MCP23017(i2c, address=0x21)

# Define Taster pins for each motor
motor_taster_pins = {
	'Parterre': {
		'mcp': mcp0,
		'pins': [12, 13, 14]  # Taster PA_auto, PA_aus, PA_hand
	},
	'Unteres Becken': {
		'mcp': mcp1,
		'pins': [0, 1, 2]  # Taster UB_auto, UB_aus, UB_hand
	},
	'Oberes Becken': {
		'mcp': mcp1,
		'pins': [3, 4, 5]  # Taster OB_auto, OB_aus, OB_hand
	}
}

# Define LED pins for each motor
motor_led_pins = {
	'Parterre': [0, 1, 2, 3],  # LEDs PA_active, PA_auto, PA_aus, PA_hand
	'Unteres Becken': [4, 5, 6, 7],  # LEDs UB_active, UB_auto, UB_aus, UB_hand
	'Oberes Becken': [8, 9, 10, 11],  # LEDs OB_active, OB_auto, OB_aus, OB_hand
	'Fehler': [15]  # Fehler-LED ERR_active
}

# Define Interrupt GPIOs for each MCP23017
interrupt_gpios = {
	mcp0: {'IA': 22, 'IB': 23},
	mcp1: {'IA': 24, 'IB': 25}
}

# Function to configure Taster pins
def configure_taster_pins(mcp, pins):
	taster_pins = []
	for pin_num in pins:
		pin = mcp.get_pin(pin_num)
		pin.direction = digitalio.Direction.INPUT
		pin.pull = digitalio.Pull.UP
		taster_pins.append(pin)
		print(f"Am MCP {mcp} wurde Pin {pin_num} gesetzt")
	return taster_pins

# Function to configure LED pins
def configure_led_pins(mcp, pins):
	led_pins = []
	for pin_num in pins:
		pin = mcp.get_pin(pin_num)
		pin.switch_to_output(value=False)
		led_pins.append(pin)
	return led_pins

# Configure Taster pins for each motor
for motor, config in motor_taster_pins.items():
	config['taster_pins'] = configure_taster_pins(config['mcp'], config['pins'])

# Configure LED pins for each motor
leds = {}
for motor, pins in motor_led_pins.items():
	leds[motor] = configure_led_pins(mcp0, pins)

# Enable interrupts only on specific pins
for motor, config in motor_taster_pins.items():
	mcp = config['mcp']
	pins = config['pins']
	interrupt_mask = sum(1 << pin for pin in pins)
	mcp.interrupt_enable |= interrupt_mask
	mcp.interrupt_configuration |= interrupt_mask
	print(f"Interrupt-Konfiguration für MCP {mcp}: {format(mcp.interrupt_enable, '016b')}")
	
# Configure interrupt handling
mcp0.io_control = 0x44  # Interrupt as open drain and mirrored
mcp1.io_control = 0x44  # Interrupt as open drain and mirrored

# Clear all interrupts
mcp0.clear_ints()
mcp1.clear_ints()

def interrupt_handler_pressed(port):
	print(f"Interrupt on port {port}, MCP0: {mcp0.int_flag}, MCP1: {mcp1.int_flag}")
	leds['Fehler'][0].value = True
	"""Callback function to be called when an Interrupt occurs."""
	for pin_flag in mcp0.int_flag:
		print(f"MCP0 Interrupt connected to Pin: {port}")
		print(f"MCP0 Pin number: {pin_flag} changed to: {mcp0.get_pin(pin_flag).value}")
	for pin_flag in mcp1.int_flag:
		print(f"MCP1 Interrupt connected to Pin: {port}")
		print(f"MCP1 Pin number: {pin_flag} changed to: {mcp1.get_pin(pin_flag).value}")
	time.sleep(0.2)
	leds['Fehler'][0].value = False
	mcp0.clear_ints()
	mcp1.clear_ints()

# RPi GPIO as interrupt pins configuration
for mcp, gpios in interrupt_gpios.items():
	ia_pin = gpios['IA']
	ib_pin = gpios['IB']
	
	ia_button = Button(ia_pin, pull_up=True, bounce_time=0.1)
	ib_button = Button(ib_pin, pull_up=True, bounce_time=0.1)
	
	ia_button.when_pressed = interrupt_handler_pressed
	ib_button.when_pressed = interrupt_handler_pressed
	ia_button.when_released = None
	ib_button.when_released = None

try:
	print("When button is pressed you'll see a message")
	time.sleep(120)  # You could run your main while loop here.
	print("Time's up. Finished!")
finally:
	exit(1)
