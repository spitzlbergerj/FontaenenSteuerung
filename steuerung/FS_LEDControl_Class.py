import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import threading
import time

class FS_LEDControl:
	def __init__(self, led_config):
		# Initialisiert den I2C-Bus
		self.i2c = busio.I2C(board.SCL, board.SDA)
		self.leds = {}
		self.blink_threads = {}  # Um das Blinken der LEDs zu verwalten

		# Konfiguriert die LEDs basierend auf der übergebenen Konfiguration
		for unit, config in led_config.items():
			mcp_address_str = config["mcp"]
			mcp_address = int(mcp_address_str, 16)  # Konvertiert die mcp-Adresse von Hex-String zu Integer
			mcp = MCP23017(self.i2c, address=mcp_address)
			self.leds[unit] = {name: mcp.get_pin(pin) for name, pin in config.items() if name != "mcp"}
			for led in self.leds[unit].values():
				led.switch_to_output(value=False)

	def set_led(self, unit, led_name, value):
		# Setzt den Zustand der angegebenen LED
		if unit in self.leds and led_name in self.leds[unit]:
			self.leds[unit][led_name].value = value

	def blink_activity_led(self, unit, duration):
		# Lässt die Aktivitäts-LED für die angegebene Dauer blinken
		if unit in self.leds and "aktiv" in self.leds[unit]:
			led = self.leds[unit]["aktiv"]
			end_time = time.time() + duration
			while time.time() < end_time:
				led.value = not led.value
				time.sleep(0.5)  # Blinkt alle 0.5 Sekunden
			led.value = False

	def start_blink_activity_led(self, unit):
		# Startet das Blinken der Aktivitäts-LED
		if unit in self.leds and "aktiv" in self.leds[unit]:
			self.stop_blink_activity_led(unit)  # Beendet vorheriges Blinken, falls vorhanden
			led = self.leds[unit]["aktiv"]
			self.blink_threads[unit] = threading.Thread(target=self._blink_led, args=(led,))
			self.blink_threads[unit].start()

	def _blink_led(self, led):
		# Blinkt die LED kontinuierlich
		while True:
			led.value = not led.value
			time.sleep(0.5)

	def stop_blink_activity_led(self, unit):
		# Stoppt das Blinken der Aktivitäts-LED
		if unit in self.blink_threads:
			self.blink_threads[unit].do_run = False
			self.blink_threads[unit].join()
			del self.blink_threads[unit]
			self.leds[unit]["aktiv"].value = False
