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
import signal
import sys

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


def signal_handler(sig, frame):
	logging.info("Programm wird beendet. Schalte alle LEDs aus.")
	for unit_name, state_machine in fountainUnits.items():
		state_machine.led_control.set_led(unit_name, "active", False)
		state_machine.led_control.set_led(unit_name, "auto", False)
		state_machine.led_control.set_led(unit_name, "off", False)
		state_machine.led_control.set_led(unit_name, "hand", False)
	sys.exit(0)


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
	message = message.lower()

	# Sonderkommandos
	if message == 'shutdown':
		return 'shutdown', None
	elif message == 'hey':
		return 'hey', None

	if len(message) != 3:
		logging.error("Ungültiges Nachrichtenformat")
		return None, None

	command_map = {
		'a': 0,
		'0': 1,
		'h': 2,
		'1': 2,
		'b': 'block',
		'u': 'unblock',
		'-': None  # Kein Befehl
	}

	# Überprüfe jedes Zeichen und konvertiere es gemäß dem command_map
	commands = []
	for c in message:
		command = command_map.get(c)
		if command is None and c != '-':
			logging.error("Ungültiger Befehl")
			return None, None
		commands.append(command)

	return commands

def handle_command(state_machine, command, key):
	current_state = state_machine.get_current_state()
	
	# Keine Aktion ausführen, wenn der aktuelle Zustand ERROR ist
	if current_state == "ERROR":
		logging.debug(f"Keine Aktion für {key} im Zustand {current_state}")
		return
	
	# Keine Aktion ausführen, wenn der aktuelle Zustand BLOCKED ist, außer bei 'unblock'
	if current_state == "BLOCKED" and command != 'unblock':
		logging.debug(f"Keine Aktion für {key} im Zustand {current_state} außer 'unblock'")
		return
	
	if command == 0:
		if state_machine.get_current_state() == "HAND":
			starteThreadMulti(key, state_machine.to_off, state_machine.to_auto)
		else:
			starteThreadSingle(key, state_machine.to_auto)
	elif command == 1:
		starteThreadSingle(key, state_machine.to_off)
	elif command == 2:
		if state_machine.get_current_state() == "AUTO":
			starteThreadMulti(key, state_machine.to_off, state_machine.to_hand)
		else:
			starteThreadSingle(key, state_machine.to_hand)
	elif command == 'block':
		starteThreadSingle(key, state_machine.block)
	elif command == 'unblock':
		starteThreadSingle(key, state_machine.unblock)
	elif command is None:
		logging.debug(f"Keine Aktion für {key}")
	else:
		logging.error(f"Unbekannter Befehl für {key}: {command}")


def build_status_message(fountainUnits):
	message_lines = []

	# Gesamtstatus
	global_state = 'NORMAL' if all(f.global_state != 'ERROR' for f in fountainUnits.values()) else 'ERROR'
	message_lines.append(f"Gesamtstatus: {global_state}")

	# Status jeder StateMachine
	for unit_name, state_machine in fountainUnits.items():
		message_lines.append(f"{unit_name} Status: {state_machine.get_current_state()}")

		# Leuchtende LEDs
		led_status = state_machine.led_control.get_led_status(unit_name)
		led_lines = [f"{unit_name} LEDs:"] + [f"  LED {index}: {'An' if status else 'Aus'}" for index, status in led_status.items()]
		message_lines.extend(led_lines)

		# Position der Mikroschalter
		switch_status = state_machine.motor_control.get_microswitch_status(unit_name)
		switch_lines = [f"{unit_name} Mikroschalter:"] + [f"  {key}: {status}" for key, status in switch_status.items()]
		message_lines.extend(switch_lines)

	return "\n".join(message_lines)


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
	global fountainUnits
	
	# Signal-Handler für Ctrl-C
	signal.signal(signal.SIGINT, signal_handler)

	# Signal-Handler für SIGTERM, das dem Prozess geschickt wird z.B. bei shutdown
	signal.signal(signal.SIGTERM, signal_handler)

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
				handle_command(state_machine, i, key)

		# Abarbeiten der eingetroffenen MQTT Nachrichten
		if message_stack:
			logging.debug("Message Stack enthät Nachricht")
			topic, message = message_stack.pop(0)  # Erste Nachricht aus dem Stack entfernen und verarbeiten
			logging.debug(f"Verarbeite Message {message} mit Topic {topic} ")
			commands = parse_command(message)

			if commands == ('shutdown', None):
				logging.info("Raspberry shutdown now")
				# Hier den Raspberry Pi herunterfahren
				# os.system('sudo shutdown now')
			elif commands == ('hey', None):
				logging.info("Statusabfrage")
				# Erstelle und sende die Statusnachricht
				status_message = build_status_message(fountainUnits)
				mqtt.publish(cloud_mqtt_config['topic_send'], status_message)
			elif commands:
				for unit, command in zip(['FOB', 'FUB', 'FPA'], commands):
					if unit in fountainUnits:
						state_machine = fountainUnits[unit]
						if command is not None and unit not in running_threads and not 'WAIT' in state_machine.get_current_state():
							handle_command(state_machine, command, unit)
			else:
				logging.warning(f"Ungültiger Befehl: {message}")

		time.sleep(interval_taster)

if __name__ == "__main__":
	main()
