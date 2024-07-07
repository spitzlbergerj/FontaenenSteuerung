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

class FS_Communication:
	# -----------------------------------------------
	# initialization
	# -----------------------------------------------
	def __init__(self, cloud_config, client_id, command_callback):

		# Logging aus dem Hauptprogramm holen
		self.logger = logging.getLogger(self.__class__.__name__)

		self.on_message = command_callback

		try:
			self.logger.debug("Attempting to connect to the broker...")
			self.client = self.connect_mqtt(cloud_config)
			self.subscribe(self.client, self.typwandlung(cloud_config['topic_receive'], "str"))
			self.client.loop_start()

			self.logger.info("MQTT Cloud etabliert")

		except Exception as e:
			self.logger.error(f"MQTT - Fehler aufgetreten: '{e}'")
		

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

	# ---------------------------------------------------------------------------------------------
	# MQTT Broker Connect
	# ---------------------------------------------------------------------------------------------
	def connect_mqtt(self, cloud_config):

		def on_connect(client, userdata, flags, rc):
			if rc == 0:
				self.logger.debug("Connected to MQTT Broker!")
			else:
				self.logger.error("Failed to connect, return code %d\n", rc)

		MQTTuser = cloud_config['user']
		MQTTpassword = cloud_config['password']
		MQTTbroker = cloud_config['web_address']
		MQTTport = cloud_config['port']

		client = mqtt.Client()
		client.tls_set()  # Aktiviere TLS ohne spezifische Zertifikate
		client.username_pw_set(MQTTuser, MQTTpassword)
		client.on_connect = on_connect
		client.connect(MQTTbroker, MQTTport, 60)
		return client

	# ---------------------------------------------------------------------------------------------
	# Subscribe zum Topic
	# ---------------------------------------------------------------------------------------------
	def subscribe(self, client: mqtt, topic):
		client.subscribe(topic, qos=0)
		client.on_message = self.on_message


	# -----------------------------------------------
	# publish message
	# -----------------------------------------------
	def publish(self, topic, message):
		self.client.publish(topic, message)
	
