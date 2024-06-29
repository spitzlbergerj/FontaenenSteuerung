class FS_ButtonControl:
    def __init__(self, button_config):
        # Initialisiert die FS_ButtonControl-Klasse.
        # :param button_config: Ein Wörterbuch mit den Taster-Konfigurationen.
        print(button_config)
        self.buttons = button_config

    def read_button(self, unit, button_type):
        index = {"auto": 0, "aus": 1, "hand": 2}.get(button_type)
        if index is not None:
            return not self.buttons[unit][index].value  # Annahme: gedrückt ist False, nicht gedrückt ist True

    def print_all_buttons(self):
        for unit in self.buttons:
            print(f"Einheit: {unit} Taster: Auto: {self.read_button(unit, 'auto')} Aus: {self.read_button(unit, 'aus')} Hand: {self.read_button(unit, 'hand')}")
