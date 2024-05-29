#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
#
# FS_Communication_Class.py
#
# Kommuniziert mit der Außenwelt
#
# frühere Kommunikation über SMS wurde ersetzt durch Kommunikation über einen
# Cloud MQTT Broker
# 
#-------------------------------------------------------------------------------


import paho.mqtt.client as mqtt

class FS_Communication:
	def __init__(self, local_config, cloud_config, client_id, command_callback):
		# Initialisierung des lokalen MQTT Clients
		self.local_client = mqtt.Client(client_id + "_local")
		self.local_broker_address = local_config['ip_address']
		self.local_broker_port = local_config['port']
		self.local_client.on_connect = self.on_connect
		self.local_client.on_message = self.on_message
		self.command_callback = command_callback

		# Authentifizierung für lokalen Broker falls angegeben
		if 'user' in local_config and local_config['user']:
			self.local_client.username_pw_set(local_config['user'], local_config['password'])

		# Verbindung zum lokalen Broker
		self.local_client.connect(self.local_broker_address, self.local_broker_port)

		# Initialisierung des Cloud MQTT Clients
		self.cloud_client = mqtt.Client(client_id + "_cloud")
		self.cloud_broker_address = cloud_config['web_address']
		self.cloud_broker_port = cloud_config['port']
		self.cloud_client.on_connect = self.on_connect
		self.cloud_client.on_message = self.on_message

		# Authentifizierung für Cloud Broker falls angegeben
		if 'user' in cloud_config and cloud_config['user']:
			self.cloud_client.username_pw_set(cloud_config['user'], cloud_config['password'])

		# Verbindung zum Cloud Broker
		self.cloud_client.connect(self.cloud_broker_address, self.cloud_broker_port)

	def on_connect(self, client, userdata, flags, rc):
		print(f"Connected to MQTT Broker: {client._client_id}")
		client.subscribe("commands/#")
	
	def on_message(self, client, userdata, msg):
		topic = msg.topic
		message = msg.payload.decode()
		print(f"Received message: {message} on topic: {topic}")
		self.command_callback(topic, message)
	
	def publish(self, topic, message, target='local'):
		if target == 'local':
			self.local_client.publish(topic, message)
		elif target == 'cloud':
			self.cloud_client.publish(topic, message)
	
	def start(self):
		self.local_client.loop_start()
		self.cloud_client.loop_start()
	
	def stop(self):
		self.local_client.loop_stop()
		self.cloud_client.loop_stop()
		self.local_client.disconnect()
		self.cloud_client.disconnect()