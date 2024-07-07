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
		{'trigger': 'to_auto',		'source': 'AUTO',		'dest': None},

		{'trigger': 'to_hand',		'source': 'OFF',		'dest': 'HAND-WAIT',	'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_hand',		'source': 'HAND',		'dest': None},

		{'trigger': 'to_off',		'source': 'HAND',		'dest': 'OFF-WAIT',		'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_off',		'source': 'AUTO',		'dest': 'OFF-WAIT',		'conditions': 'can_transition', 'before': 'activityLED_and_turnMotor'},
		{'trigger': 'to_off',		'source': 'OFF',		'dest': None},


		{'trigger': 'wait',			'source': 'AUTO-WAIT',	'dest': 'AUTO',			'before': 'waiting'},
		{'trigger': 'wait',			'source': 'HAND-WAIT',	'dest': 'HAND',			'before': 'waiting'},
		{'trigger': 'wait',			'source': 'OFF-WAIT',	'dest': 'OFF',			'before': 'waiting'},

		{'trigger': 'block',		'source': '*',			'dest': 'BLOCKED', 		'before': 'store_state'},
		{'trigger': 'unblock',		'source': 'BLOCKED',	'dest': None, 			'before': 'restore_state'},
		{'trigger': 'error',		'source': '*',			'dest': 'ERROR'},
	]



	# -----------------------------------------------
	# Initialisierung
	# -----------------------------------------------
	def __init__(self, name, config, steuerung):
		# Initialisiert die FS_StateMachine-Klasse.
		# :param name: Der Name der Maschine (z.B. 'FOB', 'FUB', 'FPA').
		# :param steuerung: Das Steuerungswörterbuch, das alle LEDs, Taster und Schalter enthält.

		# Parameter in die Klasse übernehmen
		self.name = name

		self.wait_time = config['Zeiten']['IntervallStatus']
		self.stop_delay = config['Zeiten']['MotorStopDelay']

		self.steuerung = steuerung

		# Logging aus dem Hauptprogramm holen
		self.logger = logging.getLogger(self.__class__.__name__)

		# Logging
		self.logger.info(f"__init__: name: {name}")
		self.logger.debug(f"__init__: config: {config} steuerung: {steuerung}")

		# Initialisiert die LED- und Motorsteuerung
		self.led_control = FS_LEDControl({name: steuerung[name]['LEDs']})
		self.motor_control = FS_MotorControl(config, steuerung)
		self.button_control = FS_ButtonControl({name: steuerung[name]['Taster']})
		self.logger.info(f"__init__: LEDs, Motor, Taster erfolgreich initialisiert")

		# setzen von Klassen Variablen
		self.global_state = 'NORMAL'  # Globaler Zustand für Fehlerbehandlung
		self.lock = threading.Lock()
		self.timer = None
		self.stored_state = None
		self.last_direction = 0  # Letzte Bewegungsrichtung des Motors

		# Machine Variable setzen und ersten on_enter aufrufen
		self.state = 'INIT'
		# manuell Aufrufen notwendig, da Initialisieren mit INIT keinen "on enter" Callback auslöst
		self.init_leds_on_enter(None)
		
		# -----------------------------------------------
		# Initialisierung der Zustandsmaschine und der weiteren Steuerungen
		# -----------------------------------------------
		# self.fountainUnit = Machine(model=self, states=FS_StateMachine.states, transitions=FS_StateMachine.transitions, initial='INIT', on_exception='handle_error', queued=True, send_event=True)
		self.fountainUnit = Machine(model=self, states=FS_StateMachine.states, transitions=FS_StateMachine.transitions, initial='INIT', queued=True, send_event=True)
		self.logger.info(f"__init__: State Machine erfolgreich initialisiert")


	# ======================================================================================================================
	# Hilfsfunktionen
	# ======================================================================================================================

	# -----------------------------------------------
	# get_direction: Ermittle die Drehrichtung
	# -----------------------------------------------
	def get_direction(self, source, destination):
		self.logger.debug(f"get_direction: Status: {self.state} Source: {source} Destination: {destination}")

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

	# -----------------------------------------------
	# get_current_state: Aktueller Status
	# -----------------------------------------------
	def get_current_state(self):
		return self.state


	# ======================================================================================================================
	# Machine Funktionen
	# ======================================================================================================================

	# -----------------------------------------------
	# handle_error: Fehlerbehandlung der StateMachine
	# -----------------------------------------------
	def handle_error(self, event):
		self.logger.ERROR(f"Exception handle error: {self.state} Error: {event.error} event: {event}")

		# (noch) keine echte Fehlerbehandlung - zunächst Fehler einfach löschen
		del event.error
		return True

	# -----------------------------------------------
	# can_transition: Überprüft, ob die Zustandsmaschine in den nächsten Zustand wechseln kann
	# -----------------------------------------------
	def can_transition(self, event):
		trigger = event.event.name
		destination = event.transition.dest

		self.logger.debug(f"can_transition: durch Trigger {trigger} von Status {self.state} nach Status {destination} bei GlobalState {self.global_state}")

		return self.global_state != 'ERROR' and not self.is_in_transition()


	# -----------------------------------------------
	# init_leds_on_enter: Callback on_enter für Status INIT
	# Achtung: dieses Callback wird nicht von der Machine aufgerufen, da sie mit Init initialisiert wird und damit nie ein "on enter" ausgelöst wird
	# -----------------------------------------------
	def init_leds_on_enter(self, event):
		self.logger.debug(f"init_leds_on_enter: {self.state}")

		self.led_control.start_blink_led(self.name, 0, 0.2)
		self.led_control.start_blink_led(self.name, 1, 0.2)
		self.led_control.start_blink_led(self.name, 2, 0.2)
		self.led_control.start_blink_led(self.name, 3, 0.2)


	# -----------------------------------------------
	# init_leds_on_exit: Callback on_exit für den Status INIT
	# -----------------------------------------------
	def init_leds_on_exit(self, event):
		self.logger.debug(f"init_leds_on_enter: {self.state}")

		self.led_control.stop_blink_led(self.name, 0)
		self.led_control.stop_blink_led(self.name, 1)
		self.led_control.stop_blink_led(self.name, 2)
		self.led_control.stop_blink_led(self.name, 3)

	# -----------------------------------------------
	# manage_leds_on_enter: Aktiviere die LEDs je nach aktuellem Zustand
	# -----------------------------------------------
	def manage_leds_on_enter(self, event):
		self.logger.debug(f"manage_leds_on_enter: {self.state}")

		if self.state in ["AUTO", "OFF", "HAND"]: 
			# aktiviere die LED des Zustands
			self.led_control.stop_blink_activity_led(self.name)
			self.led_control.set_led(self.name, self.state.lower(), True)
		elif self.state in ["AUTO-WAIT", "OFF-WAIT", "HAND-WAIT"]:
			# aktiviere die LED des Zustands "ohne -WAIT"
			state_prefix = self.state.split('-')[0]
			self.led_control.set_led(self.name, state_prefix.lower(), True)
		elif self.state == "BLOCKED":
			# alle LED an
			self.led_control.set_led(self.name, "auto", True)
			self.led_control.set_led(self.name, "off", True)
			self.led_control.set_led(self.name, "hand", True)
		elif self.state == "ERROR":
			# alle LED aus
			self.led_control.set_led(self.name, "auto", False)
			self.led_control.set_led(self.name, "off", False)
			self.led_control.set_led(self.name, "hand", False)
		elif self.state == "INIT":
			# alle LED aus
			self.led_control.set_led(self.name, "auto", False)
			self.led_control.set_led(self.name, "off", False)
			self.led_control.set_led(self.name, "hand", False)
		else:
			self.logger.error(f"manage_leds_on_enter: unbekannter Status = {self.state}")


	# -----------------------------------------------
	# manage_leds_on_exit: Aktiviere die LEDs je nach zu verlassendem Zustand
	# -----------------------------------------------
	def manage_leds_on_exit(self, event):
		self.logger.debug(f"manage_leds_on_exit: {self.state}")

		if self.state in ["AUTO", "OFF", "HAND"]: 
			# aktiviere die LED des Zustands
			self.led_control.set_led(self.name, self.state.lower(), False)
		elif self.state in ["AUTO-WAIT", "OFF-WAIT", "HAND-WAIT"]:
			# nichts zu tun
			pass
		elif self.state in ["BLOCKED", "ERROR", "INIT"]:
			# alle LED an
			self.led_control.set_led(self.name, "auto", False)
			self.led_control.set_led(self.name, "off", False)
			self.led_control.set_led(self.name, "hand", False)
		else:
			self.logger.error(f"manage_leds_on_exit: unbekannter Status = {self.state}")

			
	# -----------------------------------------------
	# activityLED_and_turnMotor: aktiviere die Activity LED und den Motor
	# -----------------------------------------------
	def activityLED_and_turnMotor(self, event):
		trigger = event.event.name
		destination = event.transition.dest

		self.logger.debug(f"before_move - activityLED_and_turnMotor: durch Trigger {trigger} von Status {self.state} nach {destination}")
		self.led_control.start_blink_activity_led(self.name)

		self.logger.debug(f"Motor drehen in Richtung {self.get_direction(self.state, destination)} Ziel ist Mitte? {'OFF' in destination}")

		self.last_direction = self.motor_control.string_to_direction(self.get_direction(self.state, destination))
		self.motor_control.move_motor(self.name, self.last_direction, 'OFF' in destination)
		
		self.logger.debug("Statuswechsel Warten aufrufen ... ")
		self.wait()

	# -----------------------------------------------
	# waiting: warte
	# -----------------------------------------------
	def waiting(self, event):
		trigger = event.event.name
		destination = event.transition.dest
		self.logger.debug(f"before_move - waiting: durch Trigger {trigger} von Status {self.state} nach {destination}")
		time.sleep(self.wait_time)
		self.logger.debug(f"before_move - waiting: warten beendet")
		
	# -----------------------------------------------
	# can_transition: Überprüft, ob der Motor in den nächsten Zustand wechseln kann
	# -----------------------------------------------
	def store_state(self, event):
		self.stored_state = self.state
		self.logger.debug(f"Storing current state: {self.stored_state}")

	# -----------------------------------------------
	# can_transition: Überprüft, ob der Motor in den nächsten Zustand wechseln kann
	# -----------------------------------------------
	def restore_state(self, event):
		# Manuelles Setzen des gespeicherten Zustands ohne Auslösen von Callbacks
		self.logger.debug(f"Restoring stored state: {self.stored_state}")
		self.manage_leds_on_exit(event)
		self.fountainUnit.set_state(self.stored_state)
		self.manage_leds_on_enter(event)

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
		#time.sleep(0.5)  # Wartezeit
		self.motor_control.stop_motor(self.name)
		#time.sleep(0.5)  # Wartezeit
		self.motor_control.move_motor(self.name, -1, True)  # Drehe von Hand nach Aus
		#time.sleep(0.5)  # Wartezeit
		self.motor_control.stop_motor(self.name)
		self.initialize()  # Zustandsmaschine auf 'OFF' setzen
