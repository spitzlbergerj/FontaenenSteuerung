import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017
import os

# Initialisieren der I2C-Bus und MCP23017
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x21)

# Pins für Mikroschalter konfigurieren
pins = {
	1: (mcp.get_pin(8), mcp.get_pin(9)),  # B0, B1
	2: (mcp.get_pin(11), mcp.get_pin(12)), # B3, B4
	3: (mcp.get_pin(14), mcp.get_pin(15)) # B6, B7
}

# Konfigurieren Sie alle Pins als Eingänge mit Pull-Up-Widerständen
for pin_pair in pins.values():
	for pin in pin_pair:
		pin.direction = digitalio.Direction.INPUT
		pin.pull = digitalio.Pull.UP
		# pin.switch_to_input(pull_up=True)

def beep():
	# Auf Windows
	if os.name == 'nt':
		os.system('echo \a')
	# Auf MacOS und Unix-Systemen
	elif os.name == 'posix':
		os.system('printf "\a"')
	# Andere Systeme
	else:
		print('\a')

def check_switches():
	try:
		while True:
			statuses = []
			for motor, (no_pin, nc_pin) in pins.items():
				no_state = no_pin.value
				nc_state = nc_pin.value
				statuses.append(f"Motor {motor} - NO: {no_state}, NC: {nc_state}")
				if nc_state:
					beep()
			print(" | ".join(statuses))
			time.sleep(0.1)
	except KeyboardInterrupt:
		print("\nTest beendet.")

if __name__ == '__main__':
	check_switches()
