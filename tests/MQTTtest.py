import paho.mqtt.client as mqtt
import random
import time
import sys

# -----------------------------------------------
# CaravanPi File/MARIADB/MQTT library einbinden
# -----------------------------------------------
sys.path.append('/home/pi/FontaenenSteuerung/steuerung')
from FS_Files_Class import FS_Files


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

def subscribe(client: mqtt):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(MQTT_TOPIC, qos=0)
    client.on_message = on_message


fs_files = FS_Files(config_file="/home/pi/FontaenenSteuerung/defaults/config.json")
config = fs_files.config

cloud_mqtt_config = config['MQTT Cloud']
local_mqtt_config = config['MQTT lokal']

MQTT_BROKER = config['MQTT Cloud']['web_address']
MQTT_PORT = config['MQTT Cloud']['Port']
MQTT_USER = config['MQTT Cloud']['user']
MQTT_PASSWORD = config['MQTT Cloud']['password']
MQTT_TOPIC = config['MQTT Cloud']['topic_receive']
MQTT_CLIENT_ID = f"fountainController-{random.randint(0, 1000)}"

print(MQTT_BROKER)


client = None

# Verbinde zum Broker und füge Fehlerbehandlung hinzu
try:
    print("Attempting to connect to the broker...")
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
except Exception as e:
    print(f"Error connecting to the broker: {e}")


# Halte das Programm am Laufen, um Nachrichten zu empfangen
try:
    while True:
        print(".")
        time.sleep(0.5)  # Hier könnte später andere Logik hinzugefügt werden

except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.loop_stop()
    client.disconnect()
