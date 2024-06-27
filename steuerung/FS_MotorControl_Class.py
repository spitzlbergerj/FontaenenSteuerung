import time
import board
import busio
import digitalio

from adafruit_motorkit import MotorKit
from adafruit_mcp230xx.mcp23017 import MCP23017

class MotorControl:
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
			mcp_address = pins["mcp Adresse"]
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
		
		print(f"Drehe Motor {motor_name} in Richtung {direction}")

		motor = getattr(self.kit, f"motor{motor_name}")
		# motor.throttle = direction

	def stop_motor(self, motor_name):
		# Stoppt den Motor
		
		print(f"Stoppe Motor {motor_name}")
		
		motor = getattr(self.kit, f"motor{motor_name}")
		motor.throttle = 0

	def is_in_mid_position(self, motor_name):
		# Überprüft, ob der Motor in der Mittelposition ist (NO-Schalter ist offen)
		
		print(f"Ist Motor {motor_name} in Mittelstellung? {not self.microswitches[motor_name]["no"].value}")
		
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

		motor = getattr(self.kit, f"motor{motor_name}")
		for _ in range(steps):
			#motor.throttle = direction
			time.sleep(0.02)
			#motor.throttle = 0
			time.sleep(0.02)
