#!/usr/bin/python3
# coding=utf-8
#
# --------------------------------------------------------------------------------
#
# fontaenensteuerung.py
#
# Funktion: 
# ==========
# zentrales Skript für die Steuerung der Fontänenanlage mit folgenden Funktionen
# - Aufbau der Kommunikation zum Cloud MQTT Broker
#    - um remote Kommandos zu empfangen
#    - um Statusnachrichten zu versenden
#
# - Aufbau der Kommunikation zum lokalen MQTT Broker
#    - um anderen Skripten der Steuerung neue Zusände mitzuteilen (LED, Motoren)
#
# - State-Machine
#
# Änderungshistorie:
# ===================
# - Version 1.0.0: Initiale Version
#
# Autor:
# =======
# - Josef Spitzlberger 
# - Robert Kaiser (hardwaretechnische Realisierung und Aufbau)
#
# Datum:
# =======
# - Mai 2024
#-------------------------------------------------------------------------------

import sys
import argparse
import logging

# -----------------------------------------------
# Fontänensteuerung Libraries einbinden
# -----------------------------------------------
sys.path.append('/home/pi/FontaenenSteuerung/.lib')
from FS_Communication_Class import FS_Communication
from FS_Files_Class import FS_Files
from FS_StateMachine_Class import FS_StateMachine

# Initialisierung des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Globale Variable für Motorzustandsmaschinen
motors = {}

def command_callback(topic, message):
    """
    Callback-Funktion zur Verarbeitung von empfangenen MQTT-Nachrichten.

    :param topic: Das Thema der empfangenen Nachricht.
    :param message: Der Inhalt der empfangenen Nachricht.
    """
    motor_name, command = parse_command(message)
    if motor_name in motors:
        motors[motor_name].handle_command(command)
    else:
        logging.warning(f"Unbekannter Motorname: {motor_name}")

def parse_command(message):
    """
    Parst eine empfangene Nachricht, um den Motorname und den Befehl zu extrahieren.

    :param message: Die empfangene Nachricht.
    :return: Ein Tupel bestehend aus dem Motorname und dem Befehl.
    """
    parts = message.split(':')
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]

def main():
    # Argumente und Parameter abfragen
    parser = argparse.ArgumentParser(description='Skript zur Abfrage des EMQX Cloud Brokers und des lokalen Mosquitto Brokers nach neuen Kommandos')
    parser.add_argument('--config_file', type=str, help='Pfad zur Konfigurationsdatei')
    args = parser.parse_args()
    
    # Konfigurationsdatei laden
    fs_files = FS_Files(config_file=args.config_file)
    local_mqtt_config = fs_files.get_local_mqtt_config()
    cloud_mqtt_config = fs_files.get_cloud_mqtt_config()

    # MQTT-Client initialisieren
    mqtt_client = MQTTClient(local_mqtt_config['ip_address'], cloud_mqtt_config['web_address'], 'Fontaenensteuerung', command_callback)
    
    # Zustandsmaschinen für die Motoren initialisieren
    global motors
    motors = {
        'FOB': MotorStateMachine('FOB', mqtt_client),
        'FUB': MotorStateMachine('FUB', mqtt_client),
        'FPA': MotorStateMachine('FPA', mqtt_client)
    }
    
    # Starten des MQTT-Clients zum Empfangen von Nachrichten
    mqtt_client.start()

if __name__ == "__main__":
    main()