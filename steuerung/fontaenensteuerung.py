#!/usr/bin/env python3
# Skript zur Abfrage des EMQX Cloud Brokers und des lokalen Mosquitto Brokers nach neuen Kommandos und zur Verwaltung der Fontänensteuerung
#
# Funktion:
# Dieses Skript abonniert MQTT-Nachrichten vom EMQX Cloud Broker und vom lokalen Mosquitto Broker und verarbeitet neue Kommandos für die Fontänensteuerung. 
# Es verwaltet die Zustandsmaschine für die Motorsteuerung und nutzt MQTT zur Kommunikation und zum Senden von Steuerungsbefehlen an die Motoren und LEDs.
#
# Änderungshistorie:
# - Version 1.0.0: Initiale Version
#
# Autor:
# - [Dein Name]
#
# Datum:
# - [Aktuelles Datum]

import argparse
import logging
import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017


# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
from FS_Communication_Class import FS_Communication
from FS_Files_Class import FS_Files
from FS_StateMachine_Class import FS_StateMachine

# -----------------------------------------------
# globale Variablen
# -----------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Globale Variable für Motorzustandsmaschinen
motors = {}

# -----------------------------------------------
# Callback-Funktion zur Verarbeitung von empfangenen MQTT-Nachrichten
# -----------------------------------------------
def command_callback(topic, message):
	# Parst das empfangene Kommando und extrahiert den Motorname und den Befehl
	motor_name, command = parse_command(message)
	if motor_name in motors:
		motors[motor_name].handle_command(command)
	else:
		logging.warning(f"Unbekannter Motorname: {motor_name}")

# -----------------------------------------------
# Funktion zur Befehlsanalyse
# -----------------------------------------------
def parse_command(message):
	# Parst eine empfangene Nachricht, um den Motorname und den Befehl zu extrahieren
	parts = message.split(':')
	if len(parts) != 2:
		logging.error("Ungültiges Nachrichtenformat")
		return None, None
	return parts[0], parts[1]


def testfunktion():
	i2c = busio.I2C(board.SCL, board.SDA)
	mcp0 = MCP23017(i2c, address=0x20)
	mcp1 = MCP23017(i2c, address=0x21)
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

	taster_dict = {
	Tast_PA_auto: {"name": "Tast_PA_auto"},
	Tast_PA_aus: {"name": "Tast_PA_aus"},
	Tast_PA_hand: {"name": "Tast_PA_hand"},
	Tast_UB_auto: {"name": "Tast_UB_auto"},
	Tast_UB_aus: {"name": "Tast_UB_aus"},
	Tast_UB_hand: {"name": "Tast_UB_hand"},
	Tast_OB_auto: {"name": "Tast_OB_auto"},
	Tast_OB_aus: {"name": "Tast_OB_aus"},
	Tast_OB_hand: {"name": "Tast_OB_hand"}
	}

	while True:
		for button, config in taster_dict.items():
			if not button.value:
				print(f"Taster {config['name']} gedrückt!")


# -----------------------------------------------
# Hauptfunktion
# -----------------------------------------------
def main():
	# Argumente und Parameter abfragen
	parser = argparse.ArgumentParser(description='Skript zur Abfrage des EMQX Cloud Brokers und des lokalen Mosquitto Brokers nach neuen Kommandos')
	parser.add_argument('--config_file', type=str, help='Pfad zur Konfigurationsdatei')
	args = parser.parse_args()
	
	# Konfigurationsdatei laden
	fs_files = FS_Files(config_file=args.config_file)
	config = fs_files.config
	cloud_mqtt_config = config['MQTT Cloud']
	local_mqtt_config = config['MQTT lokal']

	# Logging der geladenen Konfiguration
	#logging.info(f"Cloud MQTT-Konfiguration: {cloud_mqtt_config}")
	#logging.info(f"Lokale MQTT-Konfiguration: {local_mqtt_config}")
	#logging.info(f"Wartezeit für Status-Intervalle: {config['Zeiten']['IntervallStatus']} Sekunden")
	#logging.info(f"Motor-Stop-Verzögerung: {config['Zeiten']['MotorStopDelay']} Sekunden")
	#logging.info(f"LED-Konfiguration: {config['LEDs']}")
	#logging.info(f"Motor-Konfiguration: {config['Microswitch']}")
	#logging.info(f"Taster-Konfiguration: {config['Taster']}")
	
	# MQTT-Client initialisieren
	#fs_comm = FS_Communication(local_mqtt_config, cloud_mqtt_config, 'Fontaenensteuerung', command_callback)
	fs_comm = None
	
	# Zustandsmaschinen für die Motoren initialisieren
	global motors
	motors = {
		'FOB': FS_StateMachine('FOB', config, fs_comm),
		'FUB': FS_StateMachine('FUB', config, fs_comm),
		'FPA': FS_StateMachine('FPA', config, fs_comm)
	}
	
	logging.info("Zustandsmaschinen für die Motoren initialisiert")

	# Initialisierung der Motoren beim Starten
	logging.info(f"initialisiere Motorstellung beim Starten")
	for motor in motors.values():
		logging.info(f"-- Motor: {motor}")
		motor.initialize_motor()

	logging.info("Motoren initialisiert")

	# Starten des MQTT-Clients zum Empfangen von Nachrichten
	#fs_comm.start()
	
	# Regelmäßige Abfrage der Taster
	interval_taster = config['Zeiten'].get('IntervallTaster', 0.05)
	while True:
		for motor in motors.values():
			motor.check_buttons()
		time.sleep(interval_taster)

if __name__ == "__main__":
	main()
