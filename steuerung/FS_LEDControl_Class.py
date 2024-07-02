import threading
import time

class FS_LEDControl:
    def __init__(self, led_config):
        # Initialisiert die FS_LEDControl-Klasse.
        # :param led_config: Ein Wörterbuch mit den LED-Konfigurationen.
        self.leds = led_config
        self.blink_threads = {}
        self.blink_stop_events = {}

    def start_blink_activity_led(self, unit, interval=0.5):
        led = self.leds[unit][0]  # Die erste LED ist die Aktivitäts-LED

        stop_event = threading.Event()
        self.blink_stop_events[unit] = stop_event

        blink_thread = threading.Thread(target=self._blink_led, args=(led, stop_event, interval))
        self.blink_threads[unit] = blink_thread
        blink_thread.start()

    def stop_blink_activity_led(self, unit):
        if unit in self.blink_stop_events:
            self.blink_stop_events[unit].set()
            self.blink_threads[unit].join()
            del self.blink_stop_events[unit]
            del self.blink_threads[unit]
            # Stellt sicher, dass die LED ausgeschaltet wird
            if unit in self.leds:
                self.leds[unit][0].value = False

    def set_led(self, unit, state, value):
        index = {"active": 0, "auto": 1, "aus": 2, "hand": 3}.get(state)
        if index is not None:
            self.leds[unit][index].value = value

    def _blink_led(self, led, stop_event, interval=0.5):
        while not stop_event.is_set():
            led.value = not led.value  # LED umschalten
            time.sleep(interval)  # Warten
        led.value = False  # Sicherstellen, dass die LED ausgeschaltet ist