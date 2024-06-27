import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

class FS_ButtonControl:
	def __init__(self, button_config):
		# Initialisiert den I2C-Bus
		self.i2c = busio.I2C(board.SCL, board.SDA)
		self.buttons = {}

		# Konfiguriert die Taster basierend auf der übergebenen Konfiguration
		for unit, pins in button_config.items():
			mcp_address = pins.pop("mcp")
			mcp = MCP23017(self.i2c, address=mcp_address)
			self.buttons[unit] = {name: mcp.get_pin(pin) for name, pin in pins.items()}
			for button in self.buttons[unit].values():
				button.switch_to_input(pull=digitalio.Pull.UP)

	def read_button(self, unit, button_name):
		# Liest den Zustand des angegebenen Tasters
		if unit in self.buttons and button_name in self.buttons[unit]:
			return not self.buttons[unit][button_name].value  # Da Pull-Up-Widerstand verwendet wird
		return False
