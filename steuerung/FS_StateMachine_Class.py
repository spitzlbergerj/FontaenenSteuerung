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
    # Initialisierung
    # -----------------------------------------------
    def __init__(self, name, config, steuerung, mqtt_client):
        # Initialisiert die FS_StateMachine-Klasse.
        # :param name: Der Name der Maschine (z.B. 'FOB', 'FUB', 'FPA').
        # :param steuerung: Das Steuerungswörterbuch, das alle LEDs, Taster und Schalter enthält.
        # :param mqtt_client: Der MQTT-Client zur Kommunikation.
        self.name = name
        self.steuerung = steuerung
        self.state = 'INIT'
        self.lock = threading.Lock()
        self.timer = None
        self.global_state = 'NORMAL'  # Globaler Zustand für Fehlerbehandlung
        self.mqtt_client = mqtt_client
        self.wait_time = config['Zeiten']['IntervallStatus']
        self.stop_delay = config['Zeiten']['MotorStopDelay']
        self.last_direction = 0  # Letzte Bewegungsrichtung des Motors

        # Initialisiert die LED- und Motorsteuerung
        self.led_control = FS_LEDControl({name: steuerung[name]['LEDs']})
        self.motor_control = FS_MotorControl(config)
        self.button_control = FS_ButtonControl({name: steuerung[name]['Taster']})

        # -----------------------------------------------
        # Definition der Zustände
        # -----------------------------------------------
        states = ['INIT', 'OFF', 'HAND', 'AUTO', 'BLOCKED', 'ERROR', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND', 'TO_HAND', 'TO_AUTO', 'WAIT']

        # -----------------------------------------------
        # Definition der Übergänge
        # -----------------------------------------------
        #
        # Ein Trigger hat folgende Parameter
        # trigger: Der Auslöser, der den Übergang initiiert. Dies ist typischerweise eine Methode, die aufgerufen wird.
        # source: Der Ausgangszustand, aus dem der Übergang startet.
        # dest: Der Zielzustand, in den die Maschine wechselt.
        # conditions: Eine optionale Bedingung, die erfüllt sein muss, damit der Übergang stattfindet.
        #
        transitions = [
            {'trigger': 'set_auto', 'source': 'OFF', 'dest': 'TO_AUTO', 'conditions': 'can_transition', 'after': 'start_blinking'},
            {'trigger': 'set_hand', 'source': 'OFF', 'dest': 'TO_HAND', 'conditions': 'can_transition', 'after': 'start_blinking'},
            {'trigger': 'set_off', 'source': 'HAND', 'dest': 'TO_OFF_FROM_HAND', 'conditions': 'can_transition', 'after': 'start_blinking'},
            {'trigger': 'set_off', 'source': 'AUTO', 'dest': 'TO_OFF_FROM_AUTO', 'conditions': 'can_transition', 'after': 'start_blinking'},
            {'trigger': 'block', 'source': '*', 'dest': 'BLOCKED'},
            {'trigger': 'unblock', 'source': 'BLOCKED', 'dest': 'OFF'},
            {'trigger': 'error', 'source': '*', 'dest': 'ERROR'},
            {'trigger': 'complete_transition', 'source': ['TO_AUTO', 'TO_HAND', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND'], 'dest': 'WAIT', 'after': 'start_waiting'},
            {'trigger': 'wait_complete', 'source': 'WAIT', 'dest': 'OFF', 'after': 'stop_blinking'},
            {'trigger': 'initialize', 'source': 'INIT', 'dest': 'OFF'}
        ]

        # -----------------------------------------------
        # Initialisierung der Zustandsmaschine
        # -----------------------------------------------
        self.machine = Machine(model=self, states=states, transitions=transitions, initial='INIT', queued=True)

    # -----------------------------------------------
    # can_transition: Überprüft, ob der Motor in den nächsten Zustand wechseln kann
    # -----------------------------------------------
    def can_transition(self):
        return self.global_state != 'ERROR' and not self.is_in_transition()

    # -----------------------------------------------
    # is_in_transition: Überprüft, ob der Motor sich derzeit in einem Übergangszustand befindet
    # -----------------------------------------------
    def is_in_transition(self):
        return self.state.startswith('TO_')

    # -----------------------------------------------
    # handle_command: Verarbeitet eingehende Befehle und löst Zustandsübergänge aus
    # -----------------------------------------------
    def handle_command(self, command):
        with self.lock:
            if self.global_state == 'ERROR':
                return  # Ignoriere Befehle im Fehlerzustand
            if self.state in ['BLOCKED', 'TO_AUTO', 'TO_HAND', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND']:
                return  # Ignoriere Befehle während eines Schaltvorgangs oder wenn blockiert

            try:
                if command.lower() == 'a':
                    self.set_auto()
                elif command.lower() == 'h':
                    self.set_hand()
                elif command == '0':
                    self.set_off()
                elif command == 'b':
                    self.block()
                elif command == 'u':
                    self.unblock()
            except MachineError as e:
                print(f"Fehler beim Auslösen des Ereignisses {command}: {e}")

    # -----------------------------------------------
    # check_buttons: checks the state of the buttons and triggers state transitions
    # -----------------------------------------------
    def check_buttons(self):
        self.button_control.print_all_buttons()

        print(f"Einheit: {self.name} Taster: Hand: {self.button_control.read_button(self.name, 'hand')} Aus: {self.button_control.read_button(self.name, 'aus')} Auto: {self.button_control.read_button(self.name, 'auto')} ")

    # -----------------------------------------------
    # on_enter_TO_AUTO: Aktionen beim Eintritt in den Zustand TO_AUTO
    # -----------------------------------------------
    def on_enter_TO_AUTO(self):
        self.trigger_motor_control(1)
        self.trigger_led_control()
        self.start_timer()

    # -----------------------------------------------
    # on_enter_TO_HAND: Aktionen beim Eintritt in den Zustand TO_HAND
    # -----------------------------------------------
    def on_enter_TO_HAND(self):
        self.trigger_motor_control(1)
        self.trigger_led_control()
        self.start_timer()

    # -----------------------------------------------
    # on_enter_TO_OFF_FROM_AUTO: Aktionen beim Eintritt in den Zustand TO_OFF_FROM_AUTO
    # -----------------------------------------------
    def on_enter_TO_OFF_FROM_AUTO(self):
        self.trigger_motor_control(-1)  # Drehe von Auto nach Aus
        self.trigger_led_control()
        self.start_timer()

    # -----------------------------------------------
    # on_enter_TO_OFF_FROM_HAND: Aktionen beim Eintritt in den Zustand TO_OFF_FROM_HAND
    # -----------------------------------------------
    def on_enter_TO_OFF_FROM_HAND(self):
        self.trigger_motor_control(-1)  # Drehe von Hand nach Aus
        self.trigger_led_control()
        self.start_timer()

    # -----------------------------------------------
    # start_blinking: starts the blinking of the activity LED
    # -----------------------------------------------
    def start_blinking(self):
        self.led_control.start_blink_activity_led(self.name)

    # -----------------------------------------------
    # stop_blinking: stops the blinking of the activity LED
    # -----------------------------------------------
    def stop_blinking(self):
        self.led_control.stop_blink_activity_led(self.name)

    # -----------------------------------------------
    # start_timer: Startet den Timer für die Übergangsperiode
    # -----------------------------------------------
    def start_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.wait_time, self.complete_transition)
        self.timer.start()

    # -----------------------------------------------
    # start_waiting: Startet den Timer für die Warteperiode
    # -----------------------------------------------
    def start_waiting(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(60, self.wait_complete)
        self.timer.start()

    # -----------------------------------------------
    # trigger_motor_control: sends a message to control the motor
    # -----------------------------------------------
    def trigger_motor_control(self, direction):
        topic = f"motor_control/{self.name}"
        message = f"move_to_{self.state.lower()}"
        # self.mqtt_client.publish(topic, message)
        print(f"Motorsteuerung für {self.name} im Zustand {self.state} ausgelöst")

        # Tatsächliche Motorsteuerung
        self.motor_control.move_motor(self.name, direction)
        self.last_direction = direction

        # Startet einen Thread, um den Motor nach dem Delay zu stoppen
        threading.Thread(target=self._stop_motor_after_delay, args=(direction,)).start()

    # -----------------------------------------------
    # _stop_motor_after_delay: stops the motor after a delay if needed
    # -----------------------------------------------
    def _stop_motor_after_delay(self, direction):
        time.sleep(self.stop_delay)
        self.motor_control.stop_motor(self.name)
        self._check_mid_position(direction)

    # -----------------------------------------------
    # _check_mid_position: checks if the motor reached the middle position and performs fine-tuning if necessary
    # -----------------------------------------------
    def _check_mid_position(self, direction):
        if self.motor_control.is_in_mid_position(self.name):
            self._perform_fine_tuning(direction)

    # -----------------------------------------------
    # _perform_fine_tuning: performs fine-tuning of the motor position
    # -----------------------------------------------
    def _perform_fine_tuning(self, direction):
        # Feineinstellung des Motors gemäß der Testlogik in MotorTest.py
        steps = self.motor_control.get_correction_steps(self.name, direction)
        self.motor_control.perform_fine_tuning(self.name, steps, direction)

    # -----------------------------------------------
    # trigger_led_control: sends a message to control the LEDs
    # -----------------------------------------------
    def trigger_led_control(self):
        topic = f"led_control/{self.name}"
        if self.state in ['TO_AUTO', 'TO_HAND', 'TO_OFF_FROM_AUTO', 'TO_OFF_FROM_HAND']:
            message = "blink_activity_led"
        else:
            message = f"set_led_{self.state.lower()}"
            self.led_control.set_led(self.name, self.state.lower(), True)
        #self.mqtt_client.publish(topic, message)
        print(f"LED-Ansteuerung für {self.name} im Zustand {self.state} ausgelöst")

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
        self.motor_control.move_motor(self.name, 1)  # Drehe von Auto nach Aus
        time.sleep(3)  # Beispielwartezeit für Bewegung
        self.motor_control.stop_motor(self.name)
        time.sleep(1)  # Wartezeit zwischen den Bewegungen
        self.motor_control.move_motor(self.name, -1)  # Drehe von Hand nach Aus
        time.sleep(3)  # Beispielwartezeit für Bewegung
        self.motor_control.stop_motor(self.name)
        self.initialize()  # Zustandsmaschine auf 'OFF' setzen
