import logging

class FS_ButtonControl:
	def __init__(self, button_config):
		# Initialisiert die FS_ButtonControl-Klasse.
		# :param button_config: Ein Wörterbuch mit den Taster-Konfigurationen.

		# Logging aus dem Hauptprogramm holen
		self.logger = logging.getLogger(self.__class__.__name__)

		self.logger.debug(button_config)
		self.buttons = button_config

	def read_button(self, unit, button_type):
		index = {"auto": 0, "aus": 1, "hand": 2}.get(button_type)
		if index is not None:
			return not self.buttons[unit][index].value  # Annahme: gedrückt ist False, nicht gedrückt ist True

	def print_all_buttons(self):
		status = {}
		self.logger.debug("-----------------")
		for unit in self.buttons:
			# self.logger.debug({unit: self.buttons[unit]})
			status[unit] = {}
			for i, button in enumerate(self.buttons[unit]):
				button_name = ['Auto', 'Aus', 'Hand'][i]
				status[unit][button_name] = "gedrückt" if not button.value else "nicht gedrückt"
				self.logger.debug(f"Taster {unit} {button_name}: {status[unit][button_name]}")
		self.logger.debug("-----------------")
		return status