import time
import logging
import board
import busio
import digitalio

from adafruit_motorkit import MotorKit
from adafruit_mcp230xx.mcp23017 import MCP23017

class FS_MotorControl:
	def __init__(self, config, steuerung):
		# Logging aus dem Hauptprogramm holen
		self.logger = logging.getLogger(self.__class__.__name__)

		# Initialisiert den MotorKit
		self.kit = MotorKit(i2c=busio.I2C(board.SCL, board.SDA))

		# Parameter aus der konfig extrahieren
		self.correction_config = config['KorrekturMitte']
		self.speeds = config['Geschwindigkeit']
		self.fine_tuning_interval = config['Zeiten']['IntervallMittelSchritte']
		self.motor_stop_delay = config['Zeiten']['MotorStopDelay']
	
		# Übernimmt die Mikroschalter-Konfiguration aus dem steuerung-Wörterbuch
		self.microswitches = {}
		for unit in steuerung:
			if unit != 'ERR' and 'Schalter' in steuerung[unit] and len(steuerung[unit]['Schalter']) == 2:
				self.microswitches[unit] = {
					'nc': steuerung[unit]['Schalter'][1], 
					'no': steuerung[unit]['Schalter'][0]
				}
			elif unit != 'ERR':
				self.logger.warning(f"Warnung: Einheit {unit} hat nicht die erwartete Anzahl von Schaltern.")
	
	
	def direction_to_string(self, direction):
		# Wandelt die Richtung in den entsprechenden String um.

		if direction == 1:
			return "Auto-Aus-Hand"
		elif direction == -1:
			return "Hand-Aus-Auto"
		else:
			raise ValueError("Ungültige Richtung: direction muss 1 oder -1 sein.")

	def string_to_direction(aelf, direction_string):
		# Wandelt einen String in die entsprechende Richtung um.
		
		if direction_string == "Auto-Aus-Hand":
			return 1
		elif direction_string == "Hand-Aus-Auto":
			return -1
		else:
			raise ValueError("Ungültiger Richtung-String: direction_string muss 'Auto-Aus-Hand' oder 'Hand-Aus-Auto' sein.")

	def _motor_name_to_number(self, motor_name):
		# Wandelt den Motornamen in die entsprechende Motornummer um
		mapping = {
			'FOB': 1,
			'FUB': 2,
			'FPA': 3
		}
		return mapping.get(motor_name, 1)  # Standardmäßig zu 1, wenn der Name nicht gefunden wird
	
	def print_switches_for_unit(self, unit):
		if unit not in self.microswitches:
			self.logger.debug(f"Einheit {unit} hat keine definierten Microswitches.")
			return
		
		status = {}
		self.logger.debug(f"Schalterstatus für Einheit: {unit}")
		self.logger.debug("-----------------")
		for switch_name, switch in self.microswitches[unit].items():
			switch_state = "offen" if switch.value else "geschlossen"
			status[switch_name] = switch_state
			self.logger.debug(f"Schalter {unit} {switch_name}: {switch_state}")
		self.logger.debug("-----------------")
		return status
	
	def move_motor(self, motor_name, direction, target_mid_position=False):
		self.print_switches_for_unit(motor_name)

		if target_mid_position and self.is_in_mid_position(motor_name):
			self.logger.debug(f"Motor {motor_name} befindet sich bereits in der Mittelstellung. Bewegung nicht erforderlich.")
			return

		motor_number = self._motor_name_to_number(motor_name)
		self.logger.debug(f"Drehe Motor {motor_name} - {motor_number} in Richtung {self.direction_to_string(direction)}")

		motor = getattr(self.kit, f"motor{motor_number}")
		motor.throttle = direction * self.speeds[motor_name]

		start_time = time.time()  # Startzeit erfassen

		# beim Anfahren kurz warten, damit der Null Schalter wieder in open gehen könnte
		time.sleep(0.5)

		while not self.is_in_mid_position(motor_name):
			if time.time() - start_time > self.motor_stop_delay:  # Überprüfen, ob die Delay Sekunden vergangen sind
				self.logger.debug(f"Zeitbegrenzung erreicht. Motor {motor_name} wird gestoppt.")
				break
			time.sleep(0.01)  # Kurze Pause zur Überprüfung

		self.stop_motor(motor_name)
		if self.is_in_mid_position(motor_name):  # Nur Feineinstellung durchführen, wenn Mittelstellung erreicht ist
			self.perform_fine_tuning(motor_name, self.get_correction_steps(motor_name, direction), direction)

	def stop_motor(self, motor_name):
		# Stoppt den Motor
		
		self.logger.debug(f"Stoppe Motor {motor_name}")
		
		motor_number = self._motor_name_to_number(motor_name)
		motor = getattr(self.kit, f"motor{motor_number}")
		motor.throttle = 0

	def is_in_mid_position(self, motor_name):
		if motor_name in self.microswitches:
			mittelstellung = not self.microswitches[motor_name]["no"].value
			return mittelstellung
		return False

	def get_correction_steps(self, unit_name, direction):
		if direction == 1:  # Von Auto nach Aus
			return self.correction_config[unit_name]["auto-aus"]
		elif direction == -1:  # Von Hand nach Aus
			return self.correction_config[unit_name]["hand-aus"]
		return 0

	def perform_fine_tuning(self, motor_name, steps, direction):
		self.logger.debug(f"schrittweise Anpassung Motor {motor_name} in Richtung {direction} aus")

		motor_number = self._motor_name_to_number(motor_name)
		motor = getattr(self.kit, f"motor{motor_number}")
		for _ in range(steps):
			motor.throttle = direction * self.speeds[motor_name]
			time.sleep(0.02)
			motor.throttle = 0
			time.sleep(0.02)