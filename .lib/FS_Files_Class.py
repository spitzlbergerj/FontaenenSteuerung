#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
#
# FS_Files_Class.py
#
# liest und schreibt Werte aus den und in die default files
# 
#-------------------------------------------------------------------------------

import json
import datetime

class FS_Files:
	# -----------------------------------------------
	# global variables
	# -----------------------------------------------

	json_file_path = "/home/pi/FontaenenSteuerung/defaults/config.json"

	def __init__(self, config_file=None):
		self.config_file = config_file if config_file else json_file_path
		self.config = self.load_config()
	
	def load_config(self):
		try:
			with open(self.config_file, 'r') as file:
				config = json.load(file)
				return config
		except FileNotFoundError:
			print(f"Config file {self.config_file} not found.")
			return {}
		except json.JSONDecodeError:
			print(f"Error decoding JSON from the config file {self.config_file}.")
			return {}
	
	def save_config(self):
		with open(self.config_file, 'w') as file:
			json.dump(self.config, file, indent=4)
	
	def get_local_mqtt_config(self):
		return self.config.get('local_mqtt', {})
	
	def get_cloud_mqtt_config(self):
		return self.config.get('cloud_mqtt', {})
	
	def get_led_config(self, unit):
		return self.config.get('leds', {}).get(unit, {})
	
	def get_button_config(self, unit):
		return self.config.get('buttons', {}).get(unit, {})
	
	def get_authorized_users(self):
		return self.config.get('authorized_users', [])
	
	def update_config(self, section, key, value):
		if section in self.config:
			self.config[section][key] = value
			self.save_config()
		else:
			print(f"Section {section} not found in the config.")
	
	def add_authorized_user(self, phone_number):
		if 'authorized_users' in self.config:
			self.config['authorized_users'].append(phone_number)
			self.save_config()
		else:
			print("Authorized users section not found in the config.")
	
	def remove_authorized_user(self, phone_number):
		if 'authorized_users' in self.config:
			self.config['authorized_users'] = [user for user in self.config['authorized_users'] if user != phone_number]
			self.save_config()
		else:
			print("Authorized users section not found in the config.")