#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
# FS_StateMachine_Class.py
#
# Zustandsmaschine für dsie Motorsteuerung
# 
# --------------------------------------------------------------------------------

import board
import time

from transitions import Machine

from gpiozero import Button

from adafruit_mcp230xx.mcp23017 import MCP23017
from adafruit_motorkit import MotorKit
from adafruit_motor import motor

class MotorController:
	def __init__(self, motor_id):
		self.kit = MotorKit()
		self.motor = self.kit.motor[motor_id]
	
	def move_to_position(self, speed, duration):
		self.motor.throttle = speed
		time.sleep(duration)
		self.motor.throttle = 0

	def stop_motor(self):
		self.motor.throttle = 0



class LEDController:
	def __init__(self, i2c, led_pins):
		self.mcp = MCP23017(i2c)
		self.leds = [self.mcp.get_pin(pin) for pin in led_pins]
		for led in self.leds:
			led.switch_to_output(value=False)

	def set_led(self, index, state):
		self.leds[index].value = state

	def all_off(self):
		for led in self.leds:
			led.value = False



class ButtonController:
	def __init__(self, i2c_bus_num, button_pins, interrupt_pin_a, interrupt_pin_b):
		# Initialize I2C and MCP23017
		i2c = busio.I2C(board.SCL, board.SDA)
		self.mcp = MCP23017(i2c, address=i2c_bus_num)
		
		# Initialize buttons
		self.buttons = [self.mcp.get_pin(pin) for pin in button_pins]
		for button in self.buttons:
			button.switch_to_input(pull_up=True)
		
		# Setup GPIO interrupt handlers
		self.interrupt_a = Button(interrupt_pin_a)
		self.interrupt_b = Button(interrupt_pin_b)
		
		self.interrupt_a.when_pressed = self.handle_interrupt
		self.interrupt_b.when_pressed = self.handle_interrupt

	def handle_interrupt(self):
		# Check which button was pressed and handle accordingly
		for i, button in enumerate(self.buttons):
			if not button.value:
				self.on_button_press(i)
	
	def on_button_press(self, button_index):
		print(f"Button {button_index} pressed")


class FountainController:
	states = ['handbetrieb', 'aus', 'automatikbetrieb']
	
	def __init__(self, motor_controller, led_controller, button_controller):
		self.motor_controller = motor_controller
		self.led_controller = led_controller
		self.button_controller = button_controller
		
		self.machine = Machine(model=self, states=FountainController.states, initial='aus')
		self.machine.add_transition(trigger='to_handbetrieb', source='*', dest='handbetrieb', before='move_to_handbetrieb')
		self.machine.add_transition(trigger='to_aus', source='*', dest='aus', before='move_to_aus')
		self.machine.add_transition(trigger='to_automatikbetrieb', source='*', dest='automatikbetrieb', before='move_to_automatikbetrieb')
		
		self.initialize_position()
		
	def initialize_position(self):
		self.to_aus()
		self.to_aus()
		
	def move_to_handbetrieb(self):
		self.motor_controller.move_to_position(speed=1.0, duration=5)
		self.led_controller.set_led(0, True)
		
	def move_to_aus(self):
		self.motor_controller.move_to_position(speed=1.0, duration=5)
		self.led_controller.set_led(1, True)
		
	def move_to_automatikbetrieb(self):
		self.motor_controller.move_to_position(speed=1.0, duration=5)
		self.led_controller.set_led(2, True)


