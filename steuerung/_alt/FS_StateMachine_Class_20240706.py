#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
#
# FS_StateMachine_Class.py
#
# Zustandsmaschine
# 
#-------------------------------------------------------------------------------

from transitions import Machine, MachineError
import time
import logging
import threading

# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
from FS_LEDControl_Class import FS_LEDControl
from FS_MotorControl_Class import FS_MotorControl
from FS_ButtonControl_Class import FS_ButtonControl

# -----------------------------------------------
# FS_StateMachine Klassen Definition
# -----------------------------------------------
class FS_StateMachine:

	# -----------------------------------------------
	# globale Variablen
	# -----------------------------------------------
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


	# -----------------------------------------------
	# Callback execution order
	# -----------------------------------------------
	#
	# Callback						Current State		Comments
	# ---------------------------	-----------------	--------------------------------------
	# 'machine.prepare_event'		source				executed once before individual transitions are processed
	# 'transition.prepare'			source				executed as soon as the transition starts
	# 'transition.conditions'		source				conditions may fail and halt the transition
	# 'transition.unless'			source				conditions may fail and halt the transition
	# 'machine.before_state_change'	source				default callbacks declared on model
	# 'transition.before'			source	
	# 'state.on_exit'				source				callbacks declared on the source state
	# <STATE CHANGE>		
	# 'state.on_enter'				destination			callbacks declared on the destination state
	# 'transition.after'			destination	
	# 'machine.on_final'			destination			callbacks on children will be called first
	# 'machine.after_state_change'	destination			default callbacks declared on model; will also be called after internal transitions
	#
	# 'machine.on_exception'		source/destination	callbacks will be executed when an exception has been raised
	# 'machine.finalize_event'		source/destination	callbacks will be executed even if no transition took place or an exception has been raised

	states = [
		{'name': 'INIT',		'on_enter': ['init_leds_on_enter'],				'on_exit': ['init_leds_on_exit']},
		{'name': 'OFF',			'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'AUTO',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'HAND',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'AUTO-WAIT',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'HAND-WAIT',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'OFF-WAIT',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'BLOCKED',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'ERROR',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
	]

	transitions = [
		{'trigger': 'initialize',	'source': 'INIT', 		'dest': 'OFF'},

		{'trigger': 'to_auto',		'source': 'OFF',		'dest': 'AUTO-WAIT',	'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_hand',		'source': 'OFF',		'dest': 'HAND-WAIT',	'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_off',		'source': 'HAND',		'dest': 'OFF-WAIT',		'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_off',		'source': 'AUTO',		'dest': 'OFF-WAIT',		'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},

		{'trigger': 'wait',			'source': 'AUTO-WAIT',	'dest': 'AUTO',			'conditions': 'can_transition', 'after': 'waiting'},
		{'trigger': 'wait',			'source': 'HAND-WAIT',	'dest': 'HAND',			'conditions': 'can_transition', 'after': 'waiting'},
		{'trigger': 'wait',			'source': 'OFF-WAIT',	'dest': 'OFF',			'conditions': 'can_transition', 'after': 'waiting'},

		{'trigger': 'block',		'source': '*',			'dest': 'BLOCKED', 		'before': 'store_state'},
		{'trigger': 'unblock',		'source': 'BLOCKED',	'dest': None, 			'before': 'restore_state'},
		{'trigger': 'error',		'source': '*',			'dest': 'ERROR'},
	]



	# -----------------------------------------------
	# Initialisierung
	# -----------------------------------------------
	def __init__(self, name, config, steuerung, mqtt_client):
		# Initialisiert die FS_StateMachine-Klasse.
		# :param name: Der Name der Maschine (z.B. 'FOB', 'FUB', 'FPA').
		# :param steuerung: Das Steuerungswörterbuch, das alle LEDs, Taster und Schalter enthält.
		# :param mqtt_client: Der MQTT-Client zur Kommunikation.

		logging.getLogger('transitions').setLevel(logging.WARNING)

		self.name = name

		self.wait_time = config['Zeiten']['IntervallStatus']
		self.stop_delay = config['Zeiten']['MotorStopDelay']

		self.steuerung = steuerung
		self.mqtt_client = mqtt_client

		self.state = 'INIT'
		self.lock = threading.Lock()
		self.timer = None
		self.global_state = 'NORMAL'  # Globaler Zustand für Fehlerbehandlung

		# -----------------------------------------------
		# Initialisierung der Zustandsmaschine
		# -----------------------------------------------
		# self.fountainUnit = Machine(model=self, states=FS_StateMachine.states, transitions=FS_StateMachine.transitions, initial='INIT', on_exception='handle_error', queued=True, send_event=True)
		self.fountainUnit = Machine(model=self, states=FS_StateMachine.states, transitions=FS_StateMachine.transitions, initial='INIT', queued=True, send_event=True)
		
		
		self.stored_state = None
		self.last_direction = 0  # Letzte Bewegungsrichtung des Motors

		# Initialisiert die LED- und Motorsteuerung
		self.led_control = FS_LEDControl({name: steuerung[name]['LEDs']})
		self.motor_control = FS_MotorControl(config, steuerung)
		self.button_control = FS_ButtonControl({name: steuerung[name]['Taster']})

	# ======================================================================================================================
	# Hilfsfunktionen
	# ======================================================================================================================

	# -----------------------------------------------
	# get_direction: Ermittle die Drehrichtung
	# -----------------------------------------------
	def get_direction(self, source, destination):
		logging.info(f"get_direction: Status: {self.state} Source: {source} Destination: {destination}")

		if source == 'HAND' and destination == 'AUTO-WAIT':
			return "Hand-Aus-Auto"
		elif source == 'HAND' and destination == 'OFF-WAIT':
			return "Hand-Aus-Auto"
		
		elif source == 'AUTO' and destination == 'HAND-WAIT':
			return "Auto-Aus-Hand"
		elif source == 'AUTO' and destination == 'OFF-WAIT':
			return "Auto-Aus-Hand"
		
		elif source == 'OFF' and destination == 'AUTO-WAIT':
			return "Hand-Aus-Auto"
		elif source == 'OFF' and destination == 'HAND-WAIT':
			return "Auto-Aus-Hand"
		else:
			return None

	# -----------------------------------------------
	# is_in_transition: Überprüft, ob der Motor sich derzeit in einem Übergangszustand befindet
	# -----------------------------------------------
	def is_in_transition(self):
		# enthält der Status das Wort WAIT?
		# also: AUTO-WAIT, AUS-WAIT, HAND-WAIT
		# dann bereits in transition
		return 'WAIT' in self.state


	# ======================================================================================================================
	# Machine Funktionen
	# ======================================================================================================================

	# -----------------------------------------------
	# handle_error: Fehlerbehandlung der StateMachine
	# -----------------------------------------------
	def handle_error(self, event):
		logging.info(f"Exception handle error: {self.state} Error: {event.error} event: {event}")

		# (noch) keine echte Fehlerbehandlung - zunächst Fehler einfach löschen
		del event.error
		return True

	# -----------------------------------------------
	# can_transition: Überprüft, ob der Motor in den nächsten Zustand wechseln kann
	# -----------------------------------------------
	def can_transition(self, event):
		trigger = event.event.name
		destination = event.transition.dest

		logging.info(f"can_transition: durch Trigger {trigger} von Status {self.state} nach Status {destination} bei GlobalState {self.global_state}")

		return self.global_state != 'ERROR' and not self.is_in_transition()

	# -----------------------------------------------
	# handle_command: Verarbeitet eingehende Befehle und löst Zustandsübergänge aus
	# -----------------------------------------------
	def handle_command(self, command):
		with self.lock:
			if self.global_state == 'ERROR':
				return  # Ignoriere Befehle im Fehlerzustand
			if self.state in ['BLOCKED', 'TO_AUTO', 'TO_HAND', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND']:
				return  # Ignoriere Befehle während eines Schaltvorgangs oder wenn blockiert

			try:
				if command.lower() == 'a':
					self.set_auto()
				elif command.lower() == 'h':
					self.set_hand()
				elif command == '0':
					self.set_off()
				elif command == 'b':
					self.block()
				elif command == 'u':
					self.unblock()
			except MachineError as e:
				print(f"Fehler beim Auslösen des Ereignisses {command}: {e}")

	# -----------------------------------------------
	# check_buttons: checks the state of the buttons and triggers state transitions
	# -----------------------------------------------
	def check_buttons(self):
		self.button_control.print_all_buttons()
		print(f"Zustandsmaschine {self.name} im Status {self.get_current_state()}")

		# Durchlaufen Sie alle Taster der Einheit und prüfen Sie, ob sie gedrückt wurden
		for i, button in enumerate(self.steuerung[self.name]['Taster']):
			if not button.value:  # Taster ist gedrückt (value ist False)
				if i == 0:  # Auto-Taster
					self.set_auto()
				elif i == 1:  # Aus-Taster
					self.set_off()
				elif i == 2:  # Hand-Taster
					self.set_hand()
					
	def get_current_state(self):
		return self.state

	# -----------------------------------------------
	# on_enter_TO_AUTO: Aktionen beim Eintritt in den Zustand TO_AUTO
	# -----------------------------------------------
	def on_enter_TO_AUTO(self):
		self.trigger_motor_control(self.motor_control.string_to_direction("Hand-Aus-Auto"))
		self.trigger_led_control()
		self.complete_transition()

	# -----------------------------------------------
	# on_enter_TO_HAND: Aktionen beim Eintritt in den Zustand TO_HAND
	# -----------------------------------------------
	def on_enter_TO_HAND(self):
		self.trigger_motor_control(self.motor_control.string_to_direction("Auto-Aus-Hand"))
		self.trigger_led_control()
		self.complete_transition()

	# -----------------------------------------------
	# on_enter_TO_OFF_FROM_AUTO: Aktionen beim Eintritt in den Zustand TO_OFF_FROM_AUTO
	# -----------------------------------------------
	def on_enter_TO_OFF_FROM_AUTO(self):
		self.trigger_motor_control(self.motor_control.string_to_direction("Auto-Aus-Hand"))  # Drehe von Auto nach Aus
		self.trigger_led_control()
		self.complete_transition()

	# -----------------------------------------------
	# on_enter_TO_OFF_FROM_HAND: Aktionen beim Eintritt in den Zustand TO_OFF_FROM_HAND
	# -----------------------------------------------
	def on_enter_TO_OFF_FROM_HAND(self):
		self.trigger_motor_control(self.motor_control.string_to_direction("Hand-Aus-Auto"))  # Drehe von Hand nach Aus
		self.trigger_led_control()
		self.complete_transition()

	# -----------------------------------------------
	# start_blinking: starts the blinking of the activity LED
	# -----------------------------------------------
	def start_blinking(self):
		self.led_control.start_blink_activity_led(self.name)

	# -----------------------------------------------
	# stop_blinking: stops the blinking of the activity LED
	# -----------------------------------------------
	def stop_blinking(self):
		self.led_control.stop_blink_activity_led(self.name)

	# -----------------------------------------------
	# start_waiting: Startet den Timer für die Warteperiode
	# -----------------------------------------------
	def start_waiting(self):
		if self.timer:
			self.timer.cancel()
		self.timer = threading.Timer(self.wait_time, self.wait_complete)
		self.timer.start()

	# -----------------------------------------------
	# trigger_motor_control: sends a message to control the motor
	# -----------------------------------------------
	def trigger_motor_control(self, direction):
		topic = f"motor_control/{self.name}"
		message = f"move_to_{self.state.lower()}"
		# self.mqtt_client.publish(topic, message)
		print(f"Motorsteuerung für {self.name} im Zustand {self.state} ausgelöst")

		# Tatsächliche Motorsteuerung
		self.motor_control.move_motor(self.name, direction)
		self.last_direction = direction

		# Startet einen Thread, um den Motor nach dem Delay zu stoppen
		threading.Thread(target=self._stop_motor_after_delay, args=(direction,)).start()

	# -----------------------------------------------
	# _stop_motor_after_delay: stops the motor after a delay if needed
	# -----------------------------------------------
	def _stop_motor_after_delay(self, direction):
		time.sleep(self.stop_delay)
		self.motor_control.stop_motor(self.name)
		self._check_mid_position(direction)

	# -----------------------------------------------
	# _check_mid_position: checks if the motor reached the middle position and performs fine-tuning if necessary
	# -----------------------------------------------
	def _check_mid_position(self, direction):
		if self.motor_control.is_in_mid_position(self.name):
			self._perform_fine_tuning(direction)

	# -----------------------------------------------
	# _perform_fine_tuning: performs fine-tuning of the motor position
	# -----------------------------------------------
	def _perform_fine_tuning(self, direction):
		# Feineinstellung des Motors gemäß der Testlogik in MotorTest.py
		steps = self.motor_control.get_correction_steps(self.name, direction)
		self.motor_control.perform_fine_tuning(self.name, steps, direction)

	# -----------------------------------------------
	# trigger_led_control: sends a message to control the LEDs
	# -----------------------------------------------
	def trigger_led_control(self):
		topic = f"led_control/{self.name}"
		if self.state in ['TO_AUTO', 'TO_HAND', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND']:
			message = "blink_activity_led"
		else:
			message = f"set_led_{self.state.lower()}"
			self.led_control.set_led(self.name, self.state.lower(), True)
		#self.mqtt_client.publish(topic, message)
		print(f"LED-Ansteuerung für {self.name} im Zustand {self.state} ausgelöst")

	# -----------------------------------------------
	# set_global_error: Setzt den globalen Zustand auf ERROR
	# -----------------------------------------------
	def set_global_error(self):
		with self.lock:
			self.global_state = 'ERROR'

	# -----------------------------------------------
	# initialize_motor: initialisiert den Motorzustand
	# -----------------------------------------------
	def initialize_motor(self):
		self.button_control.print_all_buttons()
		print(f"Motor: {self.name}")
		self.motor_control.move_motor(self.name, 1, True)  # Drehe von Auto nach Aus
		time.sleep(3)  # Beispielwartezeit für Bewegung
		self.motor_control.stop_motor(self.name)
		time.sleep(1)  # Wartezeit zwischen den Bewegungen
		self.motor_control.move_motor(self.name, -1, True)  # Drehe von Hand nach Aus
		time.sleep(3)  # Beispielwartezeit für Bewegung
		self.motor_control.stop_motor(self.name)
		self.initialize()  # Zustandsmaschine auf 'OFF' setzen# also 
