import json

# -----------------------------------------------
# global variables
# -----------------------------------------------
json_file_path = 'config.json'

class FS_Files:
    # -----------------------------------------------
    # initialization
    # -----------------------------------------------
    def __init__(self, config_file=None):
        # Initialisiert die FS_Files-Klasse.
        # :param config_file: Der Pfad zur Konfigurationsdatei. Wenn nicht angegeben, wird die globale Variable json_file_path verwendet.
        self.config_file = config_file if config_file else json_file_path
        self.config = self.load_config()
    
    # -----------------------------------------------
    # load configuration
    # -----------------------------------------------
    def load_config(self):
        # Lädt die Konfiguration aus der JSON-Datei.
        # :return: Ein Wörterbuch, das die Konfiguration enthält.
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
    
    # -----------------------------------------------
    # save configuration
    # -----------------------------------------------
    def save_config(self):
        # Speichert die aktuelle Konfiguration in die JSON-Datei.
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file, indent=4)
    
    # -----------------------------------------------
    # get local MQTT configuration
    # -----------------------------------------------
    def get_local_mqtt_config(self):
        # Gibt die Konfiguration für den lokalen MQTT-Broker zurück.
        # :return: Ein Wörterbuch mit den Konfigurationsparametern des lokalen MQTT-Brokers.
        return self.config.get('MQTT lokal', {})
    
    # -----------------------------------------------
    # get cloud MQTT configuration
    # -----------------------------------------------
    def get_cloud_mqtt_config(self):
        # Gibt die Konfiguration für den Cloud MQTT-Broker zurück.
        # :return: Ein Wörterbuch mit den Konfigurationsparametern des Cloud MQTT-Brokers.
        return self.config.get('MQTT Cloud', {})
    
    # -----------------------------------------------
    # get LED configuration
    # -----------------------------------------------
    def get_led_config(self, unit):
        # Gibt die LED-Konfiguration für eine bestimmte Einheit zurück.
        # :param unit: Der Name der Einheit (z.B. 'FOB', 'FUB', 'FPR').
        # :return: Ein Wörterbuch mit den GPIO-Portnummern für die LEDs der angegebenen Einheit.
        return self.config.get('LEDs', {}).get(unit, {})
    
    # -----------------------------------------------
    # get button configuration
    # -----------------------------------------------
    def get_button_config(self, unit):
        # Gibt die Taster-Konfiguration für eine bestimmte Einheit zurück.
        # :param unit: Der Name der Einheit (z.B. 'FOB', 'FUB', 'FPR').
        # :return: Ein Wörterbuch mit den GPIO-Portnummern für die Taster der angegebenen Einheit.
        return self.config.get('Taster', {}).get(unit, {})
    
    # -----------------------------------------------
    # get microswitch configuration
    # -----------------------------------------------
    def get_microswitch_config(self, unit):
        # Gibt die Mikroschalter-Konfiguration für eine bestimmte Einheit zurück.
        # :param unit: Der Name der Einheit (z.B. 'FOB', 'FUB', 'FPR').
        # :return: Ein Wörterbuch mit den Pin-Nummern für die Mikroschalter der angegebenen Einheit.
        return self.config.get('Microswitch', {}).get(unit, {})
    
    # -----------------------------------------------
    # get correction configuration
    # -----------------------------------------------
    def get_correction_config(self, unit):
        # Gibt die Korrekturwerte für die Mittelstellung der Motoren zurück.
        # :param unit: Der Name der Einheit (z.B. 'FOB', 'FUB', 'FPR').
        # :return: Ein Wörterbuch mit den Korrekturwerten der angegebenen Einheit.
        return self.config.get('KorrekturMitte', {}).get(unit, {})
    
    # -----------------------------------------------
    # get time intervals
    # -----------------------------------------------
    def get_time_intervals(self):
        # Gibt die Zeitintervalle für verschiedene Überprüfungen zurück.
        # :return: Ein Wörterbuch mit den Zeitintervallen.
        return self.config.get('Zeiten', {})
    
    # -----------------------------------------------
    # get authorized users
    # -----------------------------------------------
    def get_authorized_users(self):
        # Gibt die Liste der autorisierten Nutzer zurück.
        # :return: Eine Liste der Mobiltelefonnummern der autorisierten Nutzer.
        return self.config.get('Benutzer', [])
    
    # -----------------------------------------------
    # update configuration
    # -----------------------------------------------
    def update_config(self, section, key, value):
        # Aktualisiert einen bestimmten Konfigurationswert und speichert die Konfiguration.
        # :param section: Der Abschnitt der Konfiguration (z.B. 'MQTT lokal', 'MQTT Cloud').
        # :param key: Der Schlüssel des zu aktualisierenden Werts.
        # :param value: Der neue Wert.
        if section in self.config:
            self.config[section][key] = value
            self.save_config()
        else:
            print(f"Section {section} not found in the config.")
    
    # -----------------------------------------------
    # add authorized user
    # -----------------------------------------------
    def add_authorized_user(self, phone_number):
        # Fügt einen autorisierten Nutzer hinzu und speichert die Konfiguration.
        # :param phone_number: Die Mobiltelefonnummer des hinzuzufügenden Nutzers.
        if 'Benutzer' in self.config:
            self.config['Benutzer'].append(phone_number)
            self.save_config()
        else:
            print("Authorized users section not found in the config.")
    
    # -----------------------------------------------
    # remove authorized user
    # -----------------------------------------------
    def remove_authorized_user(self, phone_number):
        # Entfernt einen autorisierten Nutzer und speichert die Konfiguration.
        # :param phone_number: Die Mobiltelefonnummer des zu entfernenden Nutzers.
        if 'Benutzer' in self.config:
            self.config['Benutzer'] = [user for user in self.config['Benutzer'] if user != phone_number]
            self.save_config()
        else:
            print("Authorized users section not found in the config.")
