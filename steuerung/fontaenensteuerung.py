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
import threading

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
# globale Variablen und Initialisierungen
# -----------------------------------------------
# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create instances of MCP23017 class for MCP0 and MCP1
mcp_devices = {
	"0x20": MCP23017(i2c, address=0x20),
	"0x21": MCP23017(i2c, address=0x21)
}

# Hardware Konfiguration, vor allem GPIO Pins
steuerung = {}

# Threads, die laufen pro StageMachine für die Statusübergänge
running_threads = {}

# Stack für empfangene MQTT Nachrichten
message_stack = []

# Globale Logging-Konfiguration
def configure_logging(program_level="DEBUG", transitions_level="ERROR"):
	logging.basicConfig(level=program_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logging.getLogger('transitions').setLevel(transitions_level)

# -----------------------------------------------
# Thread Steuerung für die Statuswechsel
# -----------------------------------------------
def starteThreadSingle(key, trigger):
	def run():
		logging.info(">>>>>>>>>>>>>>>>> ThreadSingle")
		trigger()
		del running_threads[key]
	thread = threading.Thread(target=run)
	running_threads[key] = thread
	thread.start()

def starteThreadMulti(key, trigger1, trigger2):
	def run():
		logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>> ThreadMulti >>>> 1")
		trigger1()
		logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>> ThreadMulti >>>> 2")
		trigger2()
		del running_threads[key]
	thread = threading.Thread(target=run)
	running_threads[key] = thread
	thread.start()

# -----------------------------------------------
# Initialisiereung der GPIO Pins
# -----------------------------------------------
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
# Abfrage der Taster
# -----------------------------------------------

def check_buttons(steuerung):
	for key in ["FPA", "FUB", "FOB"]:
		for i, button in enumerate(steuerung[key]["Taster"]):
			if not button.value:
				return key, i
	return None, None

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

def buttonsTest(steuerung, duration):
	start_time = time.time()
	while time.time() - start_time < duration:
		key, i = check_buttons(steuerung)
		if key != None and i != None:
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
def command_callback(client, userdata, msg):
	global message_stack
	logging.debug(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

	message_stack.append((msg.topic, msg.payload.decode()))


	#fountainUnit_name, command = parse_command(msg.payload.decode())
	#if fountainUnit_name in fountainUnits:
	#	fountainUnits[fountainUnit_name].handle_command(command)
	#else:
	#	logging.warning(f"Unbekannter Fontänenname: {fountainUnit_name}")

# -----------------------------------------------
# Funktion zur Befehlsanalyse
# -----------------------------------------------
def parse_command(message):
    # Parst eine empfangene Nachricht, um den Fontänenname und den Befehl zu extrahieren
    parts = message.split(':')
    if len(parts) != 2:
        logging.error("Ungültiges Nachrichtenformat")
        return None, None

    fountain_name = parts[0].upper()
    command_str = parts[1].lower()

    command_map = {
        'auto': 0,
        'aus': 1,
        'hand': 2
    }

    if command_str not in command_map:
        logging.error("Ungültiger Befehl")
        return None, None

    command = command_map[command_str]
    return fountain_name, command


def fountainUnit_name_to_number(fountainUnit_name):
	# Wandelt den Fontänennamen in die entsprechende Fontänennummer um
	mapping = {
		'FOB': 1,
		'FUB': 2,
		'FPA': 3
	}
	return mapping.get(fountainUnit_name, None)  # Standardmäßig zu 1, wenn der Name nicht gefunden wird
	
# -----------------------------------------------
# Hauptfunktion
# -----------------------------------------------
def main():
	global message_stack
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
	# Logging konfigurieren
	# -----------------------------------------------

	configure_logging(program_level="DEBUG", transitions_level="DEBUG")

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
		buttonsTest(steuerung, args.taster_test)
		print("Taster Test abgeschlossen")

	cloud_mqtt_config = config['MQTT Cloud']

	# Logging der geladenen Konfiguration
	logging.debug(f"Cloud MQTT-Konfiguration: {cloud_mqtt_config}")
	logging.debug(f"Wartezeit für Status-Intervalle: {config['Zeiten']['IntervallStatus']} Sekunden")
	logging.debug(f"Motor-Stop-Verzögerung: {config['Zeiten']['MotorStopDelay']} Sekunden")
	logging.debug(f"LED-Konfiguration: {config['LEDs']}")
	logging.debug(f"Motor-Konfiguration: {config['Microswitch']}")
	logging.debug(f"Taster-Konfiguration: {config['Taster']}")
	
	# MQTT-Client initialisieren
	mqtt = FS_Communication(cloud_mqtt_config, 'Fontaenensteuerung', command_callback)
	
	# Zustandsmaschinen für die Fontänen initialisieren
	global fountainUnits
	fountainUnits = {
		'FOB': FS_StateMachine('FOB', config, steuerung),
		'FUB': FS_StateMachine('FUB', config, steuerung),
		'FPA': FS_StateMachine('FPA', config, steuerung)
	}
	
	logging.info("Zustandsmaschinen für die Fontänen initialisiert")

	# Initialisierung der Motoren beim Starten
	logging.info(f"initialisiere Motorstellung beim Starten")
	for fountainUnit_name, fountainUnit in fountainUnits.items():
		logging.info(f"-- Fontäne: {fountainUnit_name}")
		fountainUnit.initialize_motor()
	
	logging.info("Motoren initialisiert")

	# Starten des MQTT-Clients zum Empfangen von Nachrichten
	#fs_comm.start()
	
	display_button_status(steuerung)

	# Regelmäßige Abfrage der Taster
	interval_taster = config['Zeiten'].get('IntervallTaster', 0.05)
	while True:
		key, i = check_buttons(steuerung)
		if key in fountainUnits:
			state_machine = fountainUnits[key]

			if key not in running_threads and not 'WAIT' in state_machine.get_current_state():
				# StatetMachine ist NICHT in einem Umschaltvorgang
				if i == 0: # Taster Automatik
					if state_machine.get_current_state() == "HAND":
						starteThreadMulti(key, state_machine.to_off, state_machine.to_auto)
					else:
						starteThreadSingle(key, state_machine.to_auto)

				elif i == 1: # Taster Aus
					starteThreadSingle(key, state_machine.to_off)

				elif i == 2: # Taster Hand/ein
					if state_machine.get_current_state() == "AUTO":
						starteThreadMulti(key, state_machine.to_off, state_machine.to_hand)
					else:
						starteThreadSingle(key, state_machine.to_hand)

				else:
					print(f"Unbekannter Zustand: {i}")

		# Abarbeiten der eingetroffenen MQTT Nachrichten
		if message_stack:
			logging.debug("Message Stack enthät Nachricht")
			topic, message = message_stack.pop(0)  # Erste Nachricht aus dem Stack entfernen und verarbeiten
			logging.debug(f"Verarbeite Message {message} mit Topic {topic} ")
			fountainUnit_name, i = parse_command(message)
			logging.debug(f"Betrifft Fontäne {fountainUnit_name} Anweisung {i}")

			if fountainUnit_name in fountainUnits:
				state_machine = fountainUnits[fountainUnit_name]

				if key not in running_threads and not 'WAIT' in state_machine.get_current_state():
					# StatetMachine ist NICHT in einem Umschaltvorgang
					if i == 0:
						if state_machine.get_current_state() == "HAND":
							starteThreadMulti(key, state_machine.to_off, state_machine.to_auto)
						else:
							starteThreadSingle(key, state_machine.to_auto)

					elif i == 1:
						starteThreadSingle(key, state_machine.to_off)

					elif i == 2:
						if state_machine.get_current_state() == "AUTO":
							starteThreadMulti(key, state_machine.to_off, state_machine.to_hand)
						else:
							starteThreadSingle(key, state_machine.to_hand)

					else:
						print(f"Unbekannter Zustand: {i}")

		time.sleep(interval_taster)

if __name__ == "__main__":
	main()
