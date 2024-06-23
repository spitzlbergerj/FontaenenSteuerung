#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
# FS_StateMachine_Class.py
#
# Zustandsmaschine für dsie Motorsteuerung
# 
# --------------------------------------------------------------------------------

import threading

class FS_StateMachine:
    def __init__(self, name, mqtt_client):
        self.name = name
        self.state = 'OFF'
        self.lock = threading.Lock()
        self.timer = None
        self.global_state = 'NORMAL'  # Globaler Zustand für Fehlerbehandlung
        self.mqtt_client = mqtt_client
    
    def handle_command(self, command):
        with self.lock:
            if self.global_state == 'ERROR':
                return  # Ignoriere Befehle im Fehlerzustand
            if self.state in ['BLOCKED', 'TO_AUTO', 'TO_HAND', 'TO_OFF']:
                return  # Ignoriere Befehle während eines Schaltvorgangs oder wenn blockiert
            
            if command.lower() == 'a':
                if self.state != 'AUTO':
                    if self.state == 'HAND':
                        self.transition_to('TO_OFF', next_state='TO_AUTO')
                    elif self.state == 'OFF':
                        self.transition_to('TO_AUTO')
            elif command.lower() == 'h':
                if self.state != 'HAND':
                    if self.state == 'AUTO':
                        self.transition_to('TO_OFF', next_state='TO_HAND')
                    elif self.state == 'OFF':
                        self.transition_to('TO_HAND')
            elif command == '0':
                if self.state not in ['OFF', 'TO_OFF']:
                    self.transition_to('TO_OFF')
            elif command == 'b':
                self.previous_state = self.state
                self.state = 'BLOCKED'
            elif command == 'u':
                self.state = self.previous_state
    
    def transition_to(self, target_state, next_state=None):
        self.previous_state = self.state
        self.state = target_state
        self.next_state = next_state
        self.trigger_motor_control()
        self.trigger_led_control()
        self.start_timer()
    
    def start_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(60.0, self.complete_transition)
        self.timer.start()
    
    def complete_transition(self):
        with self.lock:
            if self.state == 'TO_AUTO':
                self.state = 'AUTO'
            elif self.state == 'TO_HAND':
                self.state = 'HAND'
            elif self.state == 'TO_OFF':
                self.state = 'OFF'
                if self.next_state:
                    self.transition_to(self.next_state)
                    return
            self.timer = None
            self.trigger_led_control()  # Stoppen des Blinkens der Aktivitäts-LED
    
    def trigger_motor_control(self):
        # MQTT Nachricht zur Motorsteuerung senden
        topic = f"motor_control/{self.name}"
        message = f"move_to_{self.state.lower()}"
        self.mqtt_client.publish(topic, message)
        print(f"Motorsteuerung für {self.name} im Zustand {self.state} ausgelöst")
    
    def trigger_led_control(self):
        # MQTT Nachricht zur LED-Ansteuerung senden
        topic = f"led_control/{self.name}"
        if self.state in ['TO_AUTO', 'TO_HAND', 'TO_OFF']:
            message = "blink_activity_led"
        else:
            message = f"set_led_{self.state.lower()}"
        self.mqtt_client.publish(topic, message)
        print(f"LED-Ansteuerung für {self.name} im Zustand {self.state} ausgelöst")
    
    def set_global_error(self):
        with self.lock:
            self.global_state = 'ERROR'
