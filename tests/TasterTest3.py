import time
import os
import psutil
import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

# Initialize the I2C bus:
i2c = busio.I2C(board.SCL, board.SDA)

# Create instances of MCP23017 class for MCP0 and MCP1
mcp0 = MCP23017(i2c, address=0x20)
mcp1 = MCP23017(i2c, address=0x21)

# LED Pins (example pins, adjust according to your setup)
led_PA_active = mcp0.get_pin(0)
led_PA_active.switch_to_output(value=False)

led_PA_auto = mcp0.get_pin(1)
led_PA_auto.switch_to_output(value=False)

led_PA_aus = mcp0.get_pin(2)
led_PA_aus.switch_to_output(value=False)

led_PA_hand = mcp0.get_pin(3)
led_PA_hand.switch_to_output(value=False)

led_UB_active = mcp0.get_pin(4)
led_UB_active.switch_to_output(value=False)

led_UB_auto = mcp0.get_pin(5)
led_UB_auto.switch_to_output(value=False)

led_UB_aus = mcp0.get_pin(6)
led_UB_aus.switch_to_output(value=False)

led_UB_hand = mcp0.get_pin(7)
led_UB_hand.switch_to_output(value=False)

led_OB_active = mcp0.get_pin(8)
led_OB_active.switch_to_output(value=False)

led_OB_auto = mcp0.get_pin(9)
led_OB_auto.switch_to_output(value=False)

led_OB_aus = mcp0.get_pin(10)
led_OB_aus.switch_to_output(value=False)

led_OB_hand = mcp0.get_pin(11)
led_OB_hand.switch_to_output(value=False)

led_ERR_active = mcp0.get_pin(15)
led_ERR_active.switch_to_output(value=False)

# Taster Pins
Tast_PA_auto = mcp0.get_pin(12)
Tast_PA_aus = mcp0.get_pin(13)
Tast_PA_hand = mcp0.get_pin(14)

Tast_UB_auto = mcp1.get_pin(0)
Tast_UB_aus = mcp1.get_pin(1)
Tast_UB_hand = mcp1.get_pin(2)

Tast_OB_auto = mcp1.get_pin(3)
Tast_OB_aus = mcp1.get_pin(4)
Tast_OB_hand = mcp1.get_pin(5)

# Konfigurieren Sie alle Taster als Eingänge mit Pull-Up-Widerständen
for button in [Tast_PA_auto, Tast_PA_aus, Tast_PA_hand,
			   Tast_UB_auto, Tast_UB_aus, Tast_UB_hand,
			   Tast_OB_auto, Tast_OB_aus, Tast_OB_hand]:
	button.direction = digitalio.Direction.INPUT
	button.pull = digitalio.Pull.UP

# Dictionary zur einfacheren Handhabung der Taster und zugehörigen LEDs
taster_dict = {
	Tast_PA_auto: {"name": "Tast_PA_auto", "led": led_PA_auto},
	Tast_PA_aus: {"name": "Tast_PA_aus", "led": led_PA_aus},
	Tast_PA_hand: {"name": "Tast_PA_hand", "led": led_PA_hand},
	Tast_UB_auto: {"name": "Tast_UB_auto", "led": led_UB_auto},
	Tast_UB_aus: {"name": "Tast_UB_aus", "led": led_UB_aus},
	Tast_UB_hand: {"name": "Tast_UB_hand", "led": led_UB_hand},
	Tast_OB_auto: {"name": "Tast_OB_auto", "led": led_OB_auto},
	Tast_OB_aus: {"name": "Tast_OB_aus", "led": led_OB_aus},
	Tast_OB_hand: {"name": "Tast_OB_hand", "led": led_OB_hand}
}

def blink_active_led(active_led):
	# Blinken der "active" LED für 1 Sekunde
	start_time = time.time()
	while time.time() - start_time < 1:
		active_led.value = not active_led.value
		time.sleep(0.1)  # Ändern Sie die Blinkfrequenz nach Bedarf

def check_buttons():
	for button, config in taster_dict.items():
		if not button.value:
			print(f"Taster {config['name']} gedrückt!")
			# Zugehörige LED einschalten
			config['led'].value = True
			# Active LED blinken lassen
			blink_active_led(led_PA_active if button in [Tast_PA_auto, Tast_PA_aus, Tast_PA_hand]
							 else (led_UB_active if button in [Tast_UB_auto, Tast_UB_aus, Tast_UB_hand]
								   else (led_OB_active if button in [Tast_OB_auto, Tast_OB_aus, Tast_OB_hand]
										 else None)))
			# Zugehörige LED ausschalten nach dem Blinken
			config['led'].value = False

try:
	print("Zyklische Abfrage der Taster gestartet. Drücke Strg+C zum Beenden.")
	while True:
		start_time = time.time()
		check_buttons()
		loop_time = time.time() - start_time
		# Prozessorbelastung berechnen
		cpu_usage = psutil.cpu_percent(interval=None)
		if cpu_usage > 10:
			print(f"Schleifenzeit: {loop_time:.6f}s, Prozessorlast: {cpu_usage}%")
		time.sleep(0.05)  # Kurze Pause zwischen den Abfragen
except KeyboardInterrupt:
	print("\nProgramm durch Benutzer beendet.")
	# Sicherstellen, dass alle LEDs ausgeschaltet sind, wenn das Programm beendet wird
	led_PA_active.value = False
	led_PA_auto.value = False
	led_PA_aus.value = False
	led_PA_hand.value = False
	led_UB_active.value = False
	led_UB_auto.value = False
	led_UB_aus.value = False
	led_UB_hand.value = False
	led_OB_active.value = False
	led_OB_auto.value = False
	led_OB_aus.value = False
	led_OB_hand.value = False
