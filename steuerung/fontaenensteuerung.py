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

# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
from FS_Communication_Class import FS_Communication
from FS_Files_Class import FS_Files
from FS_StateMachine import FS_StateMachine

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
	cloud_mqtt_config = cloud_mqtt_config = config['MQTT Cloud']

	# Logging der geladenen Konfiguration
	logging.info(f"Lokale MQTT-Konfiguration: {local_mqtt_config}")
	logging.info(f"Cloud MQTT-Konfiguration: {cloud_mqtt_config}")
	logging.info(f"Wartezeit für Status-Intervalle: {wait_time} Sekunden")
	logging.info(f"LED-Konfiguration: {led_config}")
	logging.info(f"Motor-Konfiguration: {motor_config}")
	logging.info(f"Taster-Konfiguration: {button_config}")
	
	
	# MQTT-Client initialisieren
	fs_comm = FS_Communication(local_mqtt_config, cloud_mqtt_config, 'Fontaenensteuerung', command_callback)
	
	# Zustandsmaschinen für die Motoren initialisieren
	global motors
	motors = {
		'FOB': FS_StateMachine('FOB', config, fs_comm),
		'FUB': FS_StateMachine('FUB', config, fs_comm),
		'FPA': FS_StateMachine('FPA', config, fs_comm)
	}
	
	logging.info("Zustandsmaschinen für die Motoren initialisiert")

	# Initialisierung der Motoren
	for motor in motors.values():
		motor.initialize_motor()

	logging.info("Motoren initialisiert")

	# Starten des MQTT-Clients zum Empfangen von Nachrichten
	fs_comm.start()
	
	# Regelmäßige Abfrage der Taster
	while True:
		for motor in motors.values():
			motor.check_buttons()
		time.sleep(time_intervals.get('IntervallTaster', 0.05))

if __name__ == "__main__":
	main()
