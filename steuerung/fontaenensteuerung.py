#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
#
# fontaenensteuerung.py
#
# Funktion: 
# ==========
# zentrales Skript für die Steuerung der Fontänenanlage mit folgenden Funktionen
# - Aufbau der Kommunikation zum Cloud MQTT Broker
#    - um remote Kommandos zu empfangen
#    - um Statusnachrichten zu versenden
#
# - Aufbau der Kommunikation zum lokalen MQTT Broker
#    - um anderen Skripten der Steuerung neue Zusände mitzuteilen (LED, Motoren)
#
# - State-Machine
#
# Änderungshistorie:
# ===================
# - Version 1.0.0: Initiale Version
#
# Autor:
# =======
# - Josef Spitzlberger 
# - Robert Kaiser (hardwaretechnische Realisierung und Aufbau)
#
# Datum:
# =======
# - Mai 2024
#-------------------------------------------------------------------------------

import sys
import board
import busio

import argparse
import logging

# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
sys.path.append('/home/pi/FontaenenSteuerung/.lib')

from FS_Communication_Class import FS_Communication
from FS_Files_Class import FS_Files
from FS_StateMachine_Class import MotorController, LEDController, ButtonController, FountainController


# Initialisierung des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
	# Argumente und Parameter abfragen
	parser = argparse.ArgumentParser(description='Skript zur Abfrage des EMQX Cloud Brokers und des lokalen Mosquitto Brokers nach neuen Kommandos')
	parser.add_argument(
			'--config_file', 
			type=str, 
			default='config.json',
			help='Pfad zur Konfigurationsdatei'
	)
	args = parser.parse_args()
	
	# Konfigurationsdatei laden
	fs_files = FS_Files(config_file=f'/home/pi/fontaenensteuerung/defaults/{args.config_file}')
	local_mqtt_config = fs_files.get_local_mqtt_config()
	cloud_mqtt_config = fs_files.get_cloud_mqtt_config()

	# MQTT-Client initialisieren
	mqtt_client = FS_Communication(local_mqtt_config['ip_address'], cloud_mqtt_config['web_address'], 'Fontaenensteuerung', command_callback)
	

	# Setup I2C
	i2c = busio.I2C(board.SCL, board.SDA)

	# Instantiate controllers
	motor_controller_1 = MotorController(motor_id=1)
	motor_controller_2 = MotorController(motor_id=2)
	motor_controller_3 = MotorController(motor_id=3)

	led_controller_1 = LEDController(i2c, led_pins=[0, 1, 2])
	led_controller_2 = LEDController(i2c, led_pins=[0, 1, 2])
	led_controller_3 = LEDController(i2c, led_pins=[0, 1, 2])

	button_controller_1 = ButtonController(
		i2c_bus_num=0x20,
		button_pins=[3, 4, 5],
		interrupt_pin_a=22,
		interrupt_pin_b=23
	)
	button_controller_2 = ButtonController(
		i2c_bus_num=0x21,
		button_pins=[3, 4, 5],
		interrupt_pin_a=24,
		interrupt_pin_b=25
	)
	button_controller_3 = ButtonController(
		i2c_bus_num=0x21,
		button_pins=[3, 4, 5],
		interrupt_pin_a=24,
		interrupt_pin_b=25
	)

	# Starten des MQTT-Clients zum Empfangen von Nachrichten
	# mqtt_client.start()

	# Instantiate state machine
	fountain_controller_1 = FountainController(motor_controller_1, led_controller_1, button_controller_1)

	# Main loop
	try:
		while True:
			if button_controller_1.is_pressed(0):
				fountain_controller_1.to_handbetrieb()
			elif button_controller_1.is_pressed(1):
				fountain_controller_1.to_aus()
			elif button_controller_1.is_pressed(2):
				fountain_controller_1.to_automatikbetrieb()
			time.sleep(0.1)
	except KeyboardInterrupt:
		pass



if __name__ == "__main__":
	main()