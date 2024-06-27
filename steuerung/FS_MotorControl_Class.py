import time
import board
import busio
import digitalio

from adafruit_motorkit import MotorKit
from adafruit_mcp230xx.mcp23017 import MCP23017

class FS_MotorControl:
	def __init__(self, config):
		# Initialisiert den MotorKit
		self.kit = MotorKit(i2c=busio.I2C(board.SCL, board.SDA))

		# Parameter aus der konfig extrahieren
		motor_config = config['Microswitch']
		self.correction_config = config['KorrekturMitte']
		self.speeds = config['Geschwindigkeit']
		self.fine_tuning_interval = config['Zeiten']['IntervallMittelSchritte']
	
		# Konfiguriert die Mikroschalter basierend auf der übergebenen Konfiguration
		self.microswitches = {}
		for unit, pins in motor_config.items():
			mcp_address_str = pins["mcp Adresse"]
			mcp_address = int(mcp_address_str, 16)  # Konvertiert die mcp-Adresse von Hex-String zu Integer
			nc_pin = pins["NC Pin"]
			no_pin = pins["NO Pin"]
			mcp = MCP23017(busio.I2C(board.SCL, board.SDA), address=mcp_address)
			self.microswitches[unit] = {
				"nc": mcp.get_pin(nc_pin),
				"no": mcp.get_pin(no_pin)
			}
			for switch in self.microswitches[unit].values():
				switch.switch_to_input(pull=digitalio.Pull.UP)

	def move_motor(self, motor_name, direction):
		# Steuert den Motor in die angegebene Richtung
		
		motor_number = self._motor_name_to_number(motor_name)

		print(f"Drehe Motor {motor_name} - {motor_number} in Richtung {direction}")

		motor = getattr(self.kit, f"motor{motor_number}")
		motor.throttle = direction * self.speeds[motor_name]

	def stop_motor(self, motor_name):
		# Stoppt den Motor
		
		print(f"Stoppe Motor {motor_name}")
		
		motor_number = self._motor_name_to_number(motor_name)
		motor = getattr(self.kit, f"motor{motor_number}")
		motor.throttle = 0

	def is_in_mid_position(self, motor_name):
		# Überprüft, ob der Motor in der Mittelposition ist (NO-Schalter ist offen)
		
		mittelstellung = not self.microswitches[motor_name]["no"].value
		print(f"Ist Motor {motor_name} in Mittelstellung? {mittelstellung}")
		
		if motor_name in self.microswitches:
			return not self.microswitches[motor_name]["no"].value
		return False

	def get_correction_steps(self, unit_name, direction):
		# Bestimmt die Anzahl der Korrekturschritte basierend auf der Konfiguration
		if direction == 1:  # Von Auto nach Aus
			return self.correction_config[unit_name]["auto-aus"]
		elif direction == -1:  # Von Hand nach Aus
			return self.correction_config[unit_name]["hand-aus"]
		return 0

	def perform_fine_tuning(self, motor_name, steps, direction):
		# Führt die Feineinstellung des Motors durch
		
		print(f"schrittweise Anpassung Motor {motor_name} in Richtung {direction} aus")

		motor_number = self._motor_name_to_number(motor_name)
		motor = getattr(self.kit, f"motor{motor_number}")
		for _ in range(steps):
			motor.throttle = direction * self.speeds[motor_name]
			time.sleep(0.02)
			#motor.throttle = 0
			time.sleep(0.02)

	def _motor_name_to_number(self, motor_name):
			# Wandelt den Motornamen in die entsprechende Motornummer um
			mapping = {
				'FOB': 1,
				'FUB': 2,
				'FPA': 3
			}
			return mapping.get(motor_name, 1)  # Standardmäßig zu 1, wenn der Name nicht gefunden wird