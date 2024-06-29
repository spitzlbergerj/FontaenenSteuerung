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

#import argparse
#import logging
import time
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017


# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
#from FS_Communication_Class import FS_Communication
#from FS_Files_Class import FS_Files
#from FS_StateMachine_Class import FS_StateMachine

# -----------------------------------------------
# globale Variablen
# -----------------------------------------------
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create instances of MCP23017 class for MCP0 and MCP1
mcp0 = MCP23017(i2c, address=0x20)
mcp1 = MCP23017(i2c, address=0x21)

# -----------------------------------------------
# LEDs
# -----------------------------------------------

# Parterre
led_FPA_active = mcp0.get_pin(0)
led_FPA_active.switch_to_output(value=False)

led_FPA_auto = mcp0.get_pin(1)
led_FPA_auto.switch_to_output(value=False)

led_FPA_aus = mcp0.get_pin(2)
led_FPA_aus.switch_to_output(value=False)

led_FPA_hand = mcp0.get_pin(3)
led_FPA_hand.switch_to_output(value=False)

# unteres Becken
led_FUB_active = mcp0.get_pin(4)
led_FUB_active.switch_to_output(value=False)

led_FUB_auto = mcp0.get_pin(5)
led_FUB_auto.switch_to_output(value=False)

led_FUB_aus = mcp0.get_pin(6)
led_FUB_aus.switch_to_output(value=False)

led_FUB_hand = mcp0.get_pin(7)
led_FUB_hand.switch_to_output(value=False)

# oberes Becken
led_FOB_active = mcp0.get_pin(8)
led_FOB_active.switch_to_output(value=False)

led_FOB_auto = mcp0.get_pin(9)
led_FOB_auto.switch_to_output(value=False)

led_FOB_aus = mcp0.get_pin(10)
led_FOB_aus.switch_to_output(value=False)

led_FOB_hand = mcp0.get_pin(11)
led_FOB_hand.switch_to_output(value=False)

# Fehler-LED
led_ERR_active = mcp0.get_pin(15)
led_ERR_active.switch_to_output(value=False)

# -----------------------------------------------
# Taster
# -----------------------------------------------

Tast_FPA_auto = mcp0.get_pin(12)
Tast_FPA_aus = mcp0.get_pin(13)
Tast_FPA_hand = mcp0.get_pin(14)

Tast_FUB_auto = mcp1.get_pin(0)
Tast_FUB_aus = mcp1.get_pin(1)
Tast_FUB_hand = mcp1.get_pin(2)

Tast_FOB_auto = mcp1.get_pin(3)
Tast_FOB_aus = mcp1.get_pin(4)
Tast_FOB_hand = mcp1.get_pin(5)

# -----------------------------------------------
# Microswitch Mittelstellung
# -----------------------------------------------

Switch_FOB_NO = mcp1.get_pin(8)
Switch_FOB_NC = mcp1.get_pin(9)

Switch_FUB_NO = mcp1.get_pin(8)
Switch_FUB_NC = mcp1.get_pin(9)

Switch_FPA_NO = mcp1.get_pin(8)
Switch_FPA_NC = mcp1.get_pin(9)

# Globale Variable für alle LEDs, Taster, Switches
steuerung = {
	"FPA": {
		"LEDs": [led_FPA_active, led_FPA_auto, led_FPA_aus, led_FPA_hand],
		"Taster": [Tast_FPA_auto, Tast_FPA_aus, Tast_FPA_hand],
		"Schalter": [Switch_FPA_NO, Switch_FPA_NC]
	},
	"FUB": {
		"LEDs": [led_FUB_active, led_FUB_auto, led_FUB_aus, led_FUB_hand],
		"Taster": [Tast_FUB_auto, Tast_FUB_aus, Tast_FUB_hand],
		"Schalter": [Switch_FUB_NO, Switch_FUB_NC]
	},
	"FOB": {
		"LEDs": [led_FOB_active, led_FOB_auto, led_FOB_aus, led_FOB_hand],
		"Taster": [Tast_FOB_auto, Tast_FOB_aus, Tast_FOB_hand],
		"Schalter": [Switch_FOB_NO, Switch_FOB_NC]
	},	
	"ERR": {
		"LEDs": [led_ERR_active],
		"Taster": [],
		"Schalter": []
	}
}

# Initialisierung der Pins und Konfiguration als Input mit Pull-Up
def initialize_pins_as_input(steuerung):
	for key in steuerung:
		for taster in steuerung[key]["Taster"]:
			taster.direction = digitalio.Direction.INPUT
			taster.pull = digitalio.Pull.UP
		for schalter in steuerung[key]["Schalter"]:
			schalter.direction = digitalio.Direction.INPUT
			schalter.pull = digitalio.Pull.UP

			
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
	blink_led(steuerung["ERR"]["LEDs"][0], 10, 0.1)

	return True



# -----------------------------------------------
# Test der Taster
# -----------------------------------------------
def display_button_status(steuerung):
	status = {}
	for key in ["FPA", "FUB", "FOB"]:
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
					blink_led(steuerung[key]["LEDs"][0])
					# Zugehörige LED ausschalten nach dem Blinken
					steuerung[key]["LEDs"][i + 1].value = False
		time.sleep(0.1)  

# -----------------------------------------------
# Hauptfunktion
# -----------------------------------------------
def main():

	# Initialisiere die Taster und Switches
	initialize_pins_as_input(steuerung)

	# LED Test starten
	LEDTest(steuerung)

	display_button_status(steuerung)

	print("Taster Test ab jetzt")
	check_buttons(steuerung, 20)
	print("Taster Test abgeschlossen")

	exit()

if __name__ == "__main__":
	main()
