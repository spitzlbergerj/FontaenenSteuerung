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
    # -----------------------------------------------
    # initialization
    # -----------------------------------------------
    def __init__(self, local_config, cloud_config, client_id, command_callback):
        # Initialisierung des lokalen MQTT Clients
        self.local_client = mqtt.Client(client_id + "_local")
        self.local_broker_address = local_config['Adresse']
        self.local_broker_port = local_config['Port']
        self.local_client.on_connect = self.on_connect
        self.local_client.on_message = self.on_message
        self.command_callback = command_callback

        # Authentifizierung für lokalen Broker falls angegeben
        if 'User' in local_config and local_config['User']:
            self.local_client.username_pw_set(local_config['User'], local_config['Passwort'])

        # Verbindung zum lokalen Broker
        self.local_client.connect(self.local_broker_address, self.local_broker_port)

        # Initialisierung des Cloud MQTT Clients
        self.cloud_client = mqtt.Client(client_id + "_cloud")
        self.cloud_broker_address = cloud_config['URL']
        self.cloud_broker_port = cloud_config['Port']
        self.cloud_client.on_connect = self.on_connect
        self.cloud_client.on_message = self.on_message

        # Authentifizierung für Cloud Broker falls angegeben
        if 'User' in cloud_config and cloud_config['User']:
            self.cloud_client.username_pw_set(cloud_config['User'], cloud_config['Passwort'])

        # Verbindung zum Cloud Broker
        self.cloud_client.connect(self.cloud_broker_address, self.cloud_broker_port)

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
