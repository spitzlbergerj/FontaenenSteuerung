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
		status = {}
		print("-----------------")
		for unit in self.buttons:
			# print({unit: self.buttons[unit]})
			status[unit] = {}
			for i, button in enumerate(self.buttons[unit]):
				button_name = ['Auto', 'Aus', 'Hand'][i]
				status[unit][button_name] = "gedrückt" if not button.value else "nicht gedrückt"
				print(f"Taster {unit} {button_name}: {status[unit][button_name]}")
		print("-----------------")
		return status