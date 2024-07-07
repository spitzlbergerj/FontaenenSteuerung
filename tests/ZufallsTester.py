import paho.mqtt.client as mqtt
import random
import time
import json
import logging
import argparse
import sys
import collections

# -----------------------------------------------
# CaravanPi File/MARIADB/MQTT library einbinden
# -----------------------------------------------
sys.path.append('/home/pi/FontaenenSteuerung/steuerung')
from FS_Files_Class import FS_Files


blocked_units = collections.defaultdict(int)


# Verbindungsdetails
MQTT_BROKER = None
MQTT_PORT = None  
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_TOPIC = None 
MQTT_CLIENT_ID = f"fountainController-{random.randint(0, 1000)}"

def connect_mqtt():
	def on_connect(client, userdata, flags, rc):
		if rc == 0:
			print("Connected to MQTT Broker!")
		else:
			print("Failed to connect, return code %d\n", rc)
	# Set Connecting Client ID
	client = mqtt.Client()
	# Set CA certificate
	client.tls_set()  # Aktiviere TLS ohne spezifische Zertifikate
	client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
	client.on_connect = on_connect
	client.connect(MQTT_BROKER, MQTT_PORT, 60)
	return client


# -----------------------------------------------
# Argumente und Parameter abfragen
# -----------------------------------------------
parser = argparse.ArgumentParser(description='Zufallstester Fontänensteuerung')
parser.add_argument('--config_file', type=str, help='Pfad zur Konfigurationsdatei')
args = parser.parse_args()

# -----------------------------------------------
# Konfigurationsdatei laden
# -----------------------------------------------
# Konfigurationsdatei laden
fs_files = FS_Files(config_file=args.config_file)
config = fs_files.config

# Fontänen-Einheiten und Kommandos
units = ['FOB', 'FUB', 'FPA']
commands = ['auto', 'off', 'hand', 'block', 'unblock']

MQTT_BROKER = config['MQTT Cloud']['web_address']
MQTT_PORT = config['MQTT Cloud']['port']
MQTT_USER = config['MQTT Cloud']['user']
MQTT_PASSWORD = config['MQTT Cloud']['password']
MQTT_TOPIC = config['MQTT Cloud']['topic_receive']
MQTT_CLIENT_ID = f"fountainController-{random.randint(0, 1000)}"

client = None

# Verbinde zum Broker und füge Fehlerbehandlung hinzu
try:
	print("Attempting to connect to the broker...")
	client = connect_mqtt()
	client.loop_start()
except Exception as e:
	print(f"Error connecting to the broker: {e}")

time.sleep(3)

try:
	while True:
		message = ""
		
		for unit in ['FOB', 'FUB', 'FPA']:
			if blocked_units[unit] > 0:
				if blocked_units[unit] == 1:
					# Sende 'u' (unblock) Befehl
					message += 'u'
					blocked_units[unit] = 0
				else:
					# Setze blocked_units herunter und sende normalen Befehl
					blocked_units[unit] -= 1
					message += random.choice(['a', 'h', '0', '-'])
			else:
				# Sehr selten 'b' (block) senden
				command = random.choices(['a', 'h', '0', '-', 'b'], weights=[45, 45, 45, 45, 1])[0]
				if command == 'b':
					blocked_units[unit] = random.randint(1, 2)  # Maximal 2 Nachrichten später 'u' senden
				message += command

		# 10% Wahrscheinlichkeit für den Sonderbefehl 'hey'
		if random.random() < 0.1:
			message = 'hey'

		print(f"Sende Nachricht: {message}")

		# Nachricht veröffentlichen
		client.publish(MQTT_TOPIC, message)

		# Zufällige Wartezeit zwischen den Nachrichten
		wait_time = random.uniform(10, 30)  # Wartezeit zwischen 20 und 80 Sekunden
		
		# Zufällige Wartezeit zwischen 10 Minuten und 2 Stunden
		#wait_time = random.uniform(600, 7200)  # Wartezeit zwischen 600 Sekunden (10 Minuten) und 7200 Sekunden (2 Stunden)
			
		time.sleep(wait_time)
except KeyboardInterrupt:
	print("Programm beendet")

client.loop_stop()
client.disconnect()