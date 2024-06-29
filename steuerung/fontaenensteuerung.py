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

# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create instances of MCP23017 class for MCP0 and MCP1
mcp_devices = {
	"0x20": MCP23017(i2c, address=0x20),
	"0x21": MCP23017(i2c, address=0x21)
}

steuerung = {}

# Funktion zur Initialisierung der Pins basierend auf der Konfigurationsdatei
def initialize_pins(config):
	global steuerung

	for unit, led_config in config['LEDs'].items():
		if unit == "Status":
			continue
		steuerung[unit] = {'LEDs': [], 'Taster': [], 'Schalter': []}
		mcp = mcp_devices[led_config["mcp"]]
		steuerung[unit]['LEDs'] = [
			mcp.get_pin(led_config['aktiv']),
			mcp.get_pin(led_config['auto']),
			mcp.get_pin(led_config['aus']),
			mcp.get_pin(led_config['hand'])
		]
		for led in steuerung[unit]['LEDs']:
			led.switch_to_output(value=False)

	for unit, taster_config in config['Taster'].items():
		mcp = mcp_devices[taster_config["mcp"]]
		steuerung[unit]['Taster'] = [
			mcp.get_pin(taster_config['auto']),
			mcp.get_pin(taster_config['aus']),
			mcp.get_pin(taster_config['hand'])
		]
		for taster in steuerung[unit]['Taster']:
			taster.direction = digitalio.Direction.INPUT
			taster.pull = digitalio.Pull.UP

	for unit, switch_config in config['Microswitch'].items():
		mcp = mcp_devices[switch_config["mcp Adresse"]]
		steuerung[unit]['Schalter'] = [
			mcp.get_pin(switch_config['NO Pin']),
			mcp.get_pin(switch_config['NC Pin'])
		]
		for schalter in steuerung[unit]['Schalter']:
			schalter.direction = digitalio.Direction.INPUT
			schalter.pull = digitalio.Pull.UP

	steuerung["ERR"] = {
		"LEDs": [mcp_devices[config['LEDs']["Status"]["mcp"]].get_pin(config['LEDs']["Status"]["fehler"])],
		"Taster": [],
		"Schalter": []
	}
	for led in steuerung["ERR"]["LEDs"]:
		led.switch_to_output(value=False)



# -----------------------------------------------
# Test der LEDs
# -----------------------------------------------
def blink_led(led, times=3, interval=0.5):
	for _ in range(times):
		led.value = not led.value
		time.sleep(interval)
		led.value = not led.value
		time.sleep(interval)
	led.value = False


def LEDTest(steuerung):
	# LEDs für FPA, FUB, FOB und ERR aktivieren
	for key in steuerung:
		for led in steuerung[key]["LEDs"]:
			led.value = True

	time.sleep(0.5)

	# LEDs für FPA, FUB und FOB deaktivieren mit Zeitverzögerung
	for key in ["FPA", "FUB", "FOB"]:
		for led in steuerung[key]["LEDs"]:
			led.value = False
			time.sleep(0.2)

	# Fehler-LED deaktivieren
	steuerung["ERR"]["LEDs"][0].value = False

	# Fehler-LED blinken lassen
	blink_led(steuerung["ERR"]["LEDs"][0], 5, 0.05)

	return True

# -----------------------------------------------
# Test der Taster
# -----------------------------------------------
def display_button_status(steuerung):
	status = {}
	for key in ["FOB", "FUB", "FPA"]:
		# print({key: steuerung[key]['Taster']})
		status[key] = {}
		for i, button in enumerate(steuerung[key]["Taster"]):
			button_name = ['Auto', 'Aus', 'Hand'][i]
			status[key][button_name] = "gedrückt" if not button.value else "nicht gedrückt"
			print(f"Taster {key} {button_name}: {status[key][button_name]}")

	return status

def check_buttons(steuerung, duration):
	start_time = time.time()
	while time.time() - start_time < duration:
		for key in ["FPA", "FUB", "FOB"]:
			for i, button in enumerate(steuerung[key]["Taster"]):
				if not button.value:
					print(f"Taster {key} {['Auto', 'Aus', 'Hand'][i]} gedrückt!")
					# Zugehörige LED einschalten
					steuerung[key]["LEDs"][i + 1].value = True
					# Active LED blinken lassen
					blink_led(steuerung[key]["LEDs"][0], 5, 0.05)
					# Zugehörige LED ausschalten nach dem Blinken
					steuerung[key]["LEDs"][i + 1].value = False
		time.sleep(0.1)  

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
	# -----------------------------------------------
	# Argumente und Parameter abfragen
	# -----------------------------------------------
	parser = argparse.ArgumentParser(description='Steuerung (vor Ort und Remote) der Fontänen in der Schlossanlage Schleißheim')
	parser.add_argument('--config_file', type=str, help='Pfad zur Konfigurationsdatei')
	parser.add_argument('-l', '--led_test', action='store_true', help='LED Test starten')
	parser.add_argument('-t', '--taster_test', type=int, help='Tastertest für eine angegebene Dauer in Sekunden starten')
	args = parser.parse_args()

	# -----------------------------------------------
	# Konfigurationsdatei laden
	# -----------------------------------------------
	# Konfigurationsdatei laden
	fs_files = FS_Files(config_file=args.config_file)
	config = fs_files.config

	# -----------------------------------------------
	# Initialisiere die Taster und Switches
	# -----------------------------------------------
	initialize_pins(config)

	# -----------------------------------------------
	# LED und Taster Test starten
	# -----------------------------------------------
	# LED-Test starten, wenn der Parameter -l gesetzt ist
	if args.led_test:
		LEDTest(steuerung)

	# Tastertest starten, wenn der Parameter -t gesetzt ist
	if args.taster_test:
		display_button_status(steuerung)
		print(f"Taster Test ab jetzt für {args.taster_test} Sekunden")
		check_buttons(steuerung, args.taster_test)
		print("Taster Test abgeschlossen")



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
		'FOB': FS_StateMachine('FOB', config, steuerung, fs_comm),
		'FUB': FS_StateMachine('FUB', config, steuerung, fs_comm),
		'FPA': FS_StateMachine('FPA', config, steuerung, fs_comm)
	}
	
	logging.info("Zustandsmaschinen für die Motoren initialisiert")

	# Initialisierung der Motoren beim Starten
	logging.info(f"initialisiere Motorstellung beim Starten")
	for motor_name, motor in motors.items():
		logging.info(f"-- Motor: {motor_name}")
		motor.initialize_motor()
	
	logging.info("Motoren initialisiert")

	# Starten des MQTT-Clients zum Empfangen von Nachrichten
	#fs_comm.start()
	
	display_button_status(steuerung)

	# Regelmäßige Abfrage der Taster
	interval_taster = config['Zeiten'].get('IntervallTaster', 0.05)
	while True:
		for motor in motors.values():
			motor.check_buttons()
		time.sleep(interval_taster)

if __name__ == "__main__":
	main()
