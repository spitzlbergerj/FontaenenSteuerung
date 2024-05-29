#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import os
from datetime import datetime

# MQTT-Broker-Einstellungen
broker_address = "localhost"
port = 1883

# Logging-Verzeichnis
log_directory_base = os.path.expanduser("/home/pi/FontaenenSteuerung/.log/mqtt")

# Callback-Funktion bei erfolgreicher Verbindung
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print("Verbindung erfolgreich")
		client.subscribe("#")  # Alle Nachrichten abonnieren
	else:
		print(f"Verbindung fehlgeschlagen mit Code {rc}")

# Callback-Funktion bei Erhalt einer Nachricht
def on_message(client, userdata, message):
	topic = message.topic
	payload = message.payload.decode('utf-8')
	save_message_to_file(topic, payload)

def save_message_to_file(topic, payload):
	try:
		# Verzeichnisstruktur aus Topic erstellen
		directory = os.path.join(log_directory_base, *topic.split('/'))
		os.makedirs(directory, exist_ok=True)
		
		# Dateipfad erstellen
		file_path = os.path.join(directory, "messages.txt")
		
		# Zeitstempel erstellen
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		# Nachricht mit Zeitstempel in Datei speichern
		with open(file_path, 'a') as file:
			file.write(f"{timestamp} - {payload}\n")
	except OSError as e:
		print(f"Fehler beim Erstellen der Verzeichnisstruktur oder beim Speichern der Nachricht: {e}")
	except Exception as e:
		print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
	
# MQTT-Client erstellen
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Verbindung zum Broker herstellen
client.connect(broker_address, port)

# Netzwerk-Schleife starten
client.loop_forever()
