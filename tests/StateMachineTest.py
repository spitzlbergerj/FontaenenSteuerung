from transitions import Machine, State
import time
import logging

class DeviceController:

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

	def __init__(self):
		logging.getLogger('transitions').setLevel(logging.WARNING)
		# self.fountainUnit = Machine(model=self, states=DeviceController.states, transitions=DeviceController.transitions, initial='INIT', on_exception='handle_error', queued=True, send_event=True)
		self.fountainUnit = Machine(model=self, states=DeviceController.states, transitions=DeviceController.transitions, initial='INIT', queued=True, send_event=True)
		self.stored_state = None

	def get_direction(self, source, destination):
		if source == 'HAND' and destination == 'AUTO-WAIT':
			return "Hand-Aus-Auto"
		elif source == 'AUTO' and destination == 'HAND-WAIT':
			return "Auto-Aus-Hand"
		elif source == 'OFF' and destination == 'AUTO-WAIT':
			return "Hand-Aus-Auto"
		elif source == 'AUTO' and destination == 'OFF-WAIT':
			return "Auto-Aus-Hand"
		elif source == 'OFF' and destination == 'HAND-WAIT':
			return "Auto-Aus-Hand"
		elif source == 'HAND' and destination == 'OFF-WAIT':
			return "Hand-Aus-Auto"
		else:
			return None


	def handle_error(self, event):
		logging.info(f"Exception handle error: {self.state} event: {event}")

		del event.error
		return True


	def can_transition(self, event):
		trigger = event.event.name
		destination = event.transition.dest

		logging.info(f"can_transition: durch Trigger {trigger} von Stastus {self.state} nach {destination}")

		return True



	def init_leds_on_enter(self, event):
		logging.info(f"init_leds_on_enter: {self.state}")

		print("mach was mit den LEDs")


	def init_leds_on_exit(self, event):
		logging.info(f"init_leds_on_enter: {self.state}")

		print("und schluss mit den LEDS")

	def manage_leds_on_enter(self, event):
		logging.info(f"manage_leds_on_enter: {self.state}")

		if self.state == 'OFF':
			print("LED off an")
		elif self.state == 'AUTO':
			print("LED Auto an")
		elif self.state == 'HAND':
			print("LED Hand an")
		elif self.state == 'AUTO-WAIT':
			print("nichts zu tun")
		elif self.state == 'OFF-WAIT':
			print("nichts zu tun")
		elif self.state == 'HAND-WAIT':
			print("nichts zu tun")
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

	def manage_leds_on_exit(self, event):
		logging.info(f"manage_leds_on_exit: {self.state}")

		if self.state == 'OFF':
			print("LED off aus")
		elif self.state == 'AUTO':
			print("LED Auto aus")
		elif self.state == 'HAND':
			print("LED Hand aus")
		elif self.state == 'AUTO-WAIT':
			print("nichts zu tun")
		elif self.state == 'OFF-WAIT':
			print("nichts zu tun")
		elif self.state == 'HAND-WAIT':
			print("nichts zu tun")
		elif self.state == 'WAIT':
			print("nix zu tun")
		elif self.state == 'INIT':
			print("alle LEDS aus")
		elif self.state == 'BLOCKED':
			print("alle LEDS aus")
		elif self.state == 'ERROR':
			print("alle LEDS aus")
		else:
			logging.error(f"manage_leds_on_exit: unbekannter Status = {self.state}")
			
	def activityLED_and_turnMotor(self, event):
		trigger = event.event.name
		destination = event.transition.dest

		logging.info(f"before_move: durch Trigger {trigger} von Stastus {self.state} nach {destination}")
		print("Aktivitäts LED blinken lassen")

		print(f"Motor drehen in Richtung {self.get_direction(self.state, destination)}")

		if destination == "OFF":
			print("Zielstatus = OFF, daher Fine-Tuning Schlüsselstellung")

		print("Statuswechsel Warten aufrufen")
		self.wait()

	def waiting(self, event):
		logging.info(f"wait: before_move: Self: {self} Source: {self.state}  Destination: {self.fountainUnit._transition_queue} Parameter:")

		print("Wartezeit läuft los ....")

		time.sleep(2)

		print("wartezeit abgelaufen ...")

	def store_state(self, event):
		self.stored_state = self.state
		logging.info(f"Storing current state: {self.stored_state}")

	def restore_state(self, event):
		# Manuelles Setzen des gespeicherten Zustands ohne Auslösen von Callbacks
		logging.info(f"Restoring stored state: {self.stored_state}")
		self.fountainUnit.set_state(self.stored_state)
		self.manage_leds_on_enter()



# Instanziieren und die Maschine testen
controller = DeviceController()
controller.initialize()


def print_menu():
	print("\nBitte wählen Sie einen Trigger aus:")
	print("1: initialize")
	print("2: to_auto")
	print("3: to_hand")
	print("4: to_off")
	print("5: wait")
	print("6: block")
	print("7: unblock")
	print("8: error")
	print("9: exit")

def execute_trigger(choice):
	if choice == 1:
		controller.initialize()
	elif choice == 2:
		controller.to_auto()
	elif choice == 3:
		controller.to_hand()
	elif choice == 4:
		controller.to_off()
	elif choice == 5:
		controller.wait()
	elif choice == 6:
		controller.block()
	elif choice == 7:
		controller.unblock()
	elif choice == 8:
		controller.error()
	elif choice == 9:
		print("Beenden...")
		return False
	else:
		print("Ungültige Wahl.")
	return True

# Interaktive Dauerschleife
running = True
while running:
	print_menu()
	print("---------------------------")
	print(f" Aktueller Status: {controller.state}")
	print("---------------------------")
	print("")
	try:
		choice = int(input("Ihre Wahl: "))
		running = execute_trigger(choice)
	except ValueError:
		print("Ungültige Eingabe. Bitte eine Nummer wählen.")