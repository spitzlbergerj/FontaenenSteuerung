import threading
import time
import logging

class FS_LEDControl:
	def __init__(self, led_config):
		# Initialisiert die FS_LEDControl-Klasse.
		# :param led_config: Ein Wörterbuch mit den LED-Konfigurationen.

		# Logging aus dem Hauptprogramm holen
		self.logger = logging.getLogger(self.__class__.__name__)

		self.logger.debug(f"FS_LEDControl __init__: LED config: {led_config}")

		self.leds = led_config
		self.blink_threads = {} # Speichert die Blink-Threads für jede LED
		self.blink_stop_events = {} # Speichert die Stopp-Ereignisse für jede LED

	def start_blink_activity_led(self, unit, interval=0.5):
		self.logger.debug(f"start_blink_activity_led: unit: {unit} Interval: {interval}")
		self.start_blink_led(unit, 0, interval) # Die erste LED =0 ist die Aktivitäts-LED

	def start_blink_led(self, unit, ledID=0, interval=0.5):
		self.logger.debug(f"start_blink_led: unit: {unit} LED-ID: {ledID} Interval: {interval}")

		led = self.leds[unit][ledID]  

		stop_event = threading.Event()
		self.blink_stop_events[(unit, ledID)] = stop_event

		blink_thread = threading.Thread(target=self._blink_led, args=(led, stop_event, interval))
		self.blink_threads[(unit, ledID)] = blink_thread
		blink_thread.start()

	def stop_blink_activity_led(self, unit):
		self.logger.debug(f"stop_blink_activity_led: unit: {unit}")
		self.stop_blink_led(unit, 0) # Die erste LED =0 ist die Aktivitäts-LED

	def stop_blink_led(self, unit, ledID=0):
		self.logger.debug(f"stop_blink_led: unit: {unit} LED-ID: {ledID}")
		key = (unit, ledID)
		if key in self.blink_stop_events:
			self.blink_stop_events[key].set()
			self.blink_threads[key].join()
			del self.blink_stop_events[key]
			del self.blink_threads[key]
			# Stellt sicher, dass die LED ausgeschaltet wird
			if unit in self.leds and ledID in self.leds[unit]:
				self.leds[unit][ledID].value = False

	def set_led(self, unit, state, value):
		self.logger.debug(f"set_led: unit: {unit} Status: {state} Wert: {value}")
		index = {"active": 0, "auto": 1, "off": 2, "hand": 3}.get(state)
		self.logger.debug(f"set_led: Index: {index}")
		if index is not None:
			self.leds[unit][index].value = value

	def get_led_status(self, unit):
		status = {}
		for index, led in enumerate(self.leds[unit]):
			status[index] = led.value
		return status

	def _blink_led(self, led, stop_event, interval=0.5):
		self.logger.debug(f"_blink_led")
		while not stop_event.is_set():
			led.value = not led.value  # LED umschalten
			time.sleep(interval)  # Warten
		led.value = False  # Sicherstellen, dass die LED ausgeschaltet ist