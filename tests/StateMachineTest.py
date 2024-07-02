from transitions import Machine, State
import time
import logging

class DeviceController:

	# -----------------------------------------------
	# globale Variablen
	# -----------------------------------------------
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

	states = [
		{'name': 'INIT',		'on_enter': ['init_leds_on_enter'],				'on_exit': ['init_leds_on_exit']},
		{'name': 'OFF',			'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'AUTO',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'HAND',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'WAIT2AUTO',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'WAIT2HAND',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
		{'name': 'WAIT2OFF',	'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'BLOCKED',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},

		{'name': 'ERROR',		'on_enter': ['manage_leds_on_enter'], 			'on_exit': ['manage_leds_on_exit']},
	]

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


	transitions = [
		{'trigger': 'initialize',	'source': 'INIT', 		'dest': 'OFF'},

		{'trigger': 'to_auto',		'source': 'OFF',		'dest': 'WAIT2AUTO',		'conditions': 'can_transition', 'before': 'before_move', 'after': 'move_motor'},
		{'trigger': 'to_hand',		'source': 'OFF',		'dest': 'WAIT2HAND',		'conditions': 'can_transition', 'before': 'before_move', 'after': 'move_motor'},
		{'trigger': 'to_off',		'source': 'HAND',		'dest': 'WAIT2OFF',		'conditions': 'can_transition', 'before': 'before_move', 'after': 'move_motor'},
		{'trigger': 'to_off',		'source': 'AUTO',		'dest': 'WAIT2OFF',		'conditions': 'can_transition', 'before': 'before_move', 'after': 'move_motor'},

		{'trigger': 'wait',			'source': 'WAIT2AUTO',	'dest': 'AUTO',		'conditions': 'can_transition', 'after': 'waiting'},
		{'trigger': 'wait',			'source': 'WAIT2HAND',	'dest': 'HAND',		'conditions': 'can_transition', 'after': 'waiting'},
		{'trigger': 'wait',			'source': 'WAIT2OFF',	'dest': 'OFF',		'conditions': 'can_transition', 'after': 'waiting'},

		{'trigger': 'block',		'source': '*',			'dest': 'BLOCKED', 'before': 'store_state'},
		{'trigger': 'unblock',		'source': 'BLOCKED',	'dest': None, 'before': 'restore_state'},
		{'trigger': 'error',		'source': '*',			'dest': 'ERROR'},
	]

	def __init__(self):
		self.fountainUnit = Machine(model=self, states=DeviceController.states, transitions=DeviceController.transitions, initial='INIT', queued=True)
		self.stored_state = None

	def can_transition(self):
		logging.info(f"can_transition: {self.state}")

		return True



	def init_leds_on_enter(self):
		logging.info(f"init_leds_on_enter: {self.state}")

		print("mach was mit den LEDs")


	def init_leds_on_exit(self):
		logging.info(f"init_leds_on_enter: {self.state}")

		print("und schluss mit den LEDS")

	def manage_leds_on_enter(self):
		logging.info(f"manage_leds_on_enter: {self.state}")

		if self.state == 'OFF':
			print("LED off an")
		elif self.state == 'AUTO':
			print("LED Auto an")
		elif self.state == 'HAND':
			print("LED Hand an")
		elif self.state == 'WAIT':
			print("nichts zu tun")
		elif self.state == 'INIT':
			print("alle LEDS blinken schnell")
		elif self.state == 'BLOCKED':
			print("alle LEDS an")
		elif self.state == 'ERROR':
			print("alle LEDS aus")
		else:
			logging.error(f"manage_leds_on_enter: unbekannter Status = {self.state}")

	def manage_leds_on_exit(self):
		logging.info(f"manage_leds_on_exit: {self.state}")

		if self.state == 'OFF':
			print("LED off aus")
		elif self.state == 'AUTO':
			print("LED Auto aus")
		elif self.state == 'HAND':
			print("LED Hand aus")
		elif self.state == 'WAIT':
			print("nix zu tun")
		elif self.state == 'INIT':
			print("alle LEDS aus")
		elif self.state == 'BLOCKED':
			print("alle LEDS aus")
		elif self.state == 'ERROR':
			print("alle LEDS aus")
		else:
			logging.error(f"manage_leds_on_enter: unbekannter Status = {self.state}")
			
	def before_move(self):
		logging.info(f"before_move: Self: {self} Source: {self.state} Destination: {self.fountainUnit._transition_queue} Parameter: ")

		print("Aktivitäts LED blinken lassen")


	def move_motor(self):
		logging.info(f"move_motor: before_move: Self: {self} Source: {self.state} Destination: {self.fountainUnit._transition_queue[0]}  Parameter:")

		print("Motor drehen")

		if "OFF" == "OFF":
			print("Zielstatus = OFF, daher Fine-Tuning Schlüsselstellung")

		print("Statuswechsel Warten aufrufen")
		self.wait()

	def waiting(self):
		logging.info(f"wait: before_move: Self: {self} Source: {self.state}  Destination: {self.fountainUnit._transition_queue} Parameter:")

		print("Wartezeit läuft los ....")

		time.sleep(2)

		print("wartezeit abgelaufen ...")

	def store_state(self):
		self.stored_state = self.state
		logging.info(f"Storing current state: {self.stored_state}")

	def restore_state(self):
		# Manuelles Setzen des gespeicherten Zustands ohne Auslösen von Callbacks
		logging.info(f"Restoring stored state: {self.stored_state}")
		self.fountainUnit.set_state(self.stored_state)



# Instanziieren und die Maschine testen
controller = DeviceController()


# Beispiel Übergänge
controller.initialize()
controller.to_auto()
time.sleep(2)
controller.to_off()
time.sleep(2)
controller.to_hand() 

# Testen des block/unblock Mechanismus
controller.block()
print(f"Aktueller Zustand nach Block: {controller.state}")

controller.unblock()
print(f"Aktueller Zustand nach Unblock: {controller.state}")

controller.error()
print(f"Aktueller Zustand nach Unblock: {controller.state}")