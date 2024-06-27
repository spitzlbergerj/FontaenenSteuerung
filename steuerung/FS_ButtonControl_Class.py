import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

class FS_ButtonControl:
	def __init__(self, button_config):

		# self.testfunktion()

		# print(button_config)

		# Initialisiert den I2C-Bus
		self.i2c = busio.I2C(board.SCL, board.SDA)
		self.buttons = {}

		# Konfiguriert die Taster basierend auf der übergebenen Konfiguration
		for unit, config in button_config.items():
			# print(f"Unit: {unit} Config: {config}")
			mcp_address_str = config["mcp"]
			mcp_address = int(mcp_address_str, 16)  # Konvertiert die mcp-Adresse von Hex-String zu Integer

			# print(f"setze MCP auf Adresse {mcp_address_str} - {mcp_address}")
			mcp = MCP23017(self.i2c, address=mcp_address)
			self.buttons[unit] = {}

			for name, pin in config.items():
				if name != "mcp":
					# print(f"Konfiguriere Pin {pin} für Taster {name} an Einheit {unit} mit MCP-Adresse {mcp_address_str}")
					button = mcp.get_pin(pin)
					button.direction = digitalio.Direction.INPUT
					button.pull = digitalio.Pull.UP
					# print(button, button.value)
					self.buttons[unit][name] = button
		
		self.print_all_buttons()

					
	def read_button(self, unit, button_name):
		# Liest den Zustand des angegebenen Tasters
		if unit in self.buttons and button_name in self.buttons[unit]:
			# print(f"Fontäne: {unit} Button: {button_name} Wert: {(not self.buttons[unit][button_name].value)}")
			return not self.buttons[unit][button_name].value  # Da Pull-Up-Widerstand verwendet wird
		return False
	
	def print_all_buttons(self):
		# Schleife über alle Einheiten (units) in self.buttons
		for unit, buttons in self.buttons.items():
			# Schleife über alle Taster (buttons) in der aktuellen Einheit
			for name, button in buttons.items():
				print(f"Unit: {unit}, Name: {name}, Value: {button.value}")


	def testfunktion(self):
		i2c = busio.I2C(board.SCL, board.SDA)
		adr1=int("0x20",16)
		adr2=int("0x21",16)
		mcp0 = MCP23017(i2c, address=adr1)
		mcp1 = MCP23017(i2c, address=adr2)

		Tast_PA_auto = mcp0.get_pin(12)
		Tast_PA_aus = mcp0.get_pin(13)
		Tast_PA_hand = mcp0.get_pin(14)

		Tast_UB_auto = mcp1.get_pin(0)
		Tast_UB_aus = mcp1.get_pin(1)
		Tast_UB_hand = mcp1.get_pin(2)

		Tast_OB_auto = mcp1.get_pin(3)
		Tast_OB_aus = mcp1.get_pin(4)
		Tast_OB_hand = mcp1.get_pin(5)

		for button in [Tast_PA_auto, Tast_PA_aus, Tast_PA_hand,
					Tast_UB_auto, Tast_UB_aus, Tast_UB_hand,
					Tast_OB_auto, Tast_OB_aus, Tast_OB_hand]:
			button.direction = digitalio.Direction.INPUT
			button.pull = digitalio.Pull.UP

		print("FOB auto", Tast_OB_auto, Tast_OB_auto.value)
		print("FOB aus", Tast_OB_aus, Tast_OB_aus.value)
		print("FOB hand", Tast_OB_hand, Tast_OB_hand.value)

		print("FUB auto", Tast_UB_auto, Tast_UB_auto.value)
		print("FUB aus", Tast_UB_aus, Tast_UB_aus.value)
		print("FUB hand", Tast_UB_hand, Tast_UB_hand.value)

		print("FPA auto", Tast_PA_auto, Tast_PA_auto.value)
		print("FPA aus", Tast_PA_aus, Tast_PA_aus.value)
		print("FPA hand", Tast_PA_hand, Tast_PA_hand.value)
