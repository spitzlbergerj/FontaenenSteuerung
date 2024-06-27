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
import logging

# -----------------------------------------------
# globale Variablen
# -----------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FS_Communication:
	# -----------------------------------------------
	# initialization
	# -----------------------------------------------
	def __init__(self, local_config, cloud_config, client_id, command_callback):

		MQTTuser = self.typwandlung(cloud_config['User'], "str")
		MQTTpassword = self.typwandlung(cloud_config['Passwort'], "str")
		MQTTbroker = self.typwandlung(cloud_config['URL'], "str")
		MQTTport = self.typwandlung(cloud_config['Port'], "int")

		self.cloud_client = None

		try:
			self.cloud_client = mqtt.Client() 
			self.cloud_client.tls_set()  # Aktiviere TLS ohne spezifische Zertifikate
			self.cloud_client.username_pw_set(MQTTuser, MQTTpassword)
			self.cloud_client.connect(MQTTbroker, MQTTport, 60)

			self.cloud_broker_address = MQTT_broker
			self.cloud_broker_port = MQTTport

			#self.cloud_client.on_connect = self.on_connect
			#self.cloud_client.on_message = self.on_message

			# Authentifizierung für Cloud Broker falls angegeben

			# Verbindung zum Cloud Broker
			self.cloud_client.connect(self.cloud_broker_address, self.cloud_broker_port, 60)
			logging.info("MQTT Cloud etabliert")

		except Error as e:
			print(f"ERROR - MQTT - Fehler aufgetreten: '{e}'")
		

	# ---------------------------------------------------------------------------------------------
	# universelle Typumwandlung
	# ---------------------------------------------------------------------------------------------
	def typwandlung(self, wert, ziel_typ):
		if ziel_typ == "int":
			return int(wert)
		elif ziel_typ == "float":
			return float(wert)
		elif ziel_typ == "bool":
			# "true", "True", "1", etc. werden als True behandelt.
			# "0" ist false
			return wert.lower() in ["true", "1", "yes"]
		elif ziel_typ == "str":
			return str(wert)
		elif ziel_typ == "list":
			# Annahme: Wert ist ein komma-separierter String
			return wert.split(',')
		elif ziel_typ == "dict":
			# Sehr einfache Implementierung; in der Praxis würde man JSON oder einen ähnlichen Ansatz verwenden
			return dict(item.split(':') for item in wert.split(','))
		else:
			raise ValueError(f"Unbekannter Zieltyp: {ziel_typ}")

	# -----------------------------------------------
	# on connect callback
	# -----------------------------------------------
	def on_connect(self, client, userdata, flags, rc):
		print(f"Connected to MQTT Broker: {client._client_id}")
		client.subscribe("commands/#")
	
	# -----------------------------------------------
	# on message callback
	# -----------------------------------------------
	def on_message(self, client, userdata, msg):
		topic = msg.topic
		message = msg.payload.decode()
		print(f"Received message: {message} on topic: {topic}")
		self.command_callback(topic, message)
	
	# -----------------------------------------------
	# publish message
	# -----------------------------------------------
	def publish(self, topic, message, target='local'):
		if target == 'local':
			self.local_client.publish(topic, message)
		elif target == 'cloud':
			self.cloud_client.publish(topic, message)
	
	# -----------------------------------------------
	# start clients
	# -----------------------------------------------
	def start(self):
		self.local_client.loop_start()
		self.cloud_client.loop_start()
	
	# -----------------------------------------------
	# stop clients
	# -----------------------------------------------
	def stop(self):
		self.local_client.loop_stop()
		self.cloud_client.loop_stop()
		self.local_client.disconnect()
		self.cloud_client.disconnect()
