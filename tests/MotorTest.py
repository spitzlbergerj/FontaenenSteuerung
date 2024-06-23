import time
import argparse
from adafruit_motorkit import MotorKit
from adafruit_mcp230xx.mcp23017 import MCP23017
import board
import busio
import digitalio
import os

# Initialisieren der MotorKit-Bibliothek
kit = MotorKit()

# Initialisieren der I2C-Bus und MCP23017
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x21)

# Pins für Mikroschalter konfigurieren
pins = {
	1: (mcp.get_pin(8), mcp.get_pin(9)),  # B0, B1
	2: (mcp.get_pin(11), mcp.get_pin(12)), # B3, B4
	3: (mcp.get_pin(14), mcp.get_pin(15)) # B6, B7
}

# Konfigurieren Sie alle Pins als Eingänge mit Pull-Up-Widerständen
for pin_pair in pins.values():
	for pin in pin_pair:
		pin.direction = digitalio.Direction.INPUT
		pin.pull = digitalio.Pull.UP

def beep():
	# Auf Windows
	if os.name == 'nt':
		os.system('echo \a')
	# Auf MacOS und Unix-Systemen
	elif os.name == 'posix':
		os.system('printf "\a"')
	# Andere Systeme
	else:
		print('\a')

def check_null_switch(motor, wait_time):
	# beim Anfahren kurz warten, damit der Null Schalter wieder in open gehen kann
	time.sleep(0.5)

	start_time = time.time()
	while time.time() - start_time < wait_time:
		no_pin, _ = pins[motor]
		no_state = no_pin.value
		if not no_state:
			beep()
			print(f"Motor {motor} - NO: {no_state}")
			return True
		time.sleep(0.01)
	return False

def run_follow_steps(motor, direction, steps, throttle_value):
	for _ in range(steps):
		motor.throttle = throttle_value
		time.sleep(0.02)
		motor.throttle = 0
		time.sleep(0.02)

def run_motor_test(speed, wait_time, follow_steps):
	motors = [kit.motor1, kit.motor2, kit.motor3]

	while True:
		try:
			motor_number = int(input("Wählen Sie den Motor (1-3): "))
			if motor_number not in [1, 2, 3]:
				print("Ungültige Eingabe. Bitte geben Sie eine Zahl zwischen 1 und 3 ein.")
				continue
			
			direction = input("Geben Sie die Drehrichtung an (r für rechts, l für links): ").lower()
			if direction not in ['r', 'l']:
				print("Ungültige Eingabe. Bitte geben Sie 'r' für rechts oder 'l' für links ein.")
				continue
			
			throttle_value = speed / 10.0
			motor = motors[motor_number - 1]
			
			if direction == 'r':
				motor.throttle = throttle_value
			elif direction == 'l':
				motor.throttle = -throttle_value
			
			print(f"Motor {motor_number} dreht {'rechts' if direction == 'r' else 'links'} mit Geschwindigkeit {speed}.")
			
			# Mikroschalter abfragen und ausgeben
			if check_null_switch(motor_number, wait_time):
				motor.throttle = 0
				print(f"Motor {motor_number} wurde gestoppt, da der NO-Kontakt ausgelöst wurde.")
				if direction == 'r':
					run_follow_steps(motor, throttle_value, follow_steps[motor_number - 1][0], throttle_value)
				elif direction == 'l':
					run_follow_steps(motor, -throttle_value, follow_steps[motor_number - 1][1], -throttle_value)
			else:
				motor.throttle = 0
				print(f"Motor {motor_number} wurde gestoppt.")

		except ValueError:
			print("Ungültige Eingabe. Bitte versuchen Sie es erneut.")
		except KeyboardInterrupt:
			print("\nTest beendet.")
			break

def main():
	parser = argparse.ArgumentParser(description="Motorsteuerung Testroutine")
	parser.add_argument(
		'--speed', 
		type=int, 
		choices=range(4, 11), 
		default=5, 
		help='Geschwindigkeit der Motoren (4-10). Standard ist 5.'
	)
	parser.add_argument(
		'--wait_time',
		type=int,
		default=5,
		help='Wartezeit für das Abfragen der Mikroschalter in Sekunden. Standard ist 5 Sekunden.'
	)
	parser.add_argument(
		'--follow_steps',
		type=int,
		nargs=6,
		default=[10, 10, 5, 5, 5, 5],
		help='Nachlaufschritte links und rechts für jeden Motor (insgesamt 6 Werte). Standard ist 0 für alle.'
	)
	args = parser.parse_args()
	
	follow_steps = [
		(args.follow_steps[0], args.follow_steps[1]),  # Motor 1: (rechts, links)
		(args.follow_steps[2], args.follow_steps[3]),  # Motor 2: (rechts, links)
		(args.follow_steps[4], args.follow_steps[5])   # Motor 3: (rechts, links)
	]

	run_motor_test(args.speed, args.wait_time, follow_steps)

if __name__ == '__main__':
	main()
