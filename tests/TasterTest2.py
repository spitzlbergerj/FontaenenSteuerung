import time
import board
import busio
from digitalio import Direction, Pull
from RPi import GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017

class LEDController:
    def __init__(self, mcp, led_pins):
        self.led_pins = [mcp.get_pin(pin) for pin in led_pins]
        for pin in self.led_pins:
            pin.switch_to_output(value=False)

    def turn_on(self, index):
        self.led_pins[index].value = True

    def turn_off(self, index):
        self.led_pins[index].value = False

    def toggle(self, index):
        self.led_pins[index].value = not self.led_pins[index].value

# Initialisierung des I2C-Busses und der MCP23017
i2c = busio.I2C(board.SCL, board.SDA)
mcp0 = MCP23017(i2c, address=0x20)
mcp1 = MCP23017(i2c, address=0x21)

# LED-Pins Konfiguration (Gruppiert)
led_pins_mcp0 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15]
led_pins_mcp1 = []  # Falls es LEDs an mcp1 gibt

# Taster-Pins Konfiguration (Gruppiert)
button_pins_mcp0 = [12, 13, 14]
button_pins_mcp1 = [0, 1, 2, 3, 4, 5]

# LED-Controller initialisieren
led_controller_mcp0 = LEDController(mcp0, led_pins_mcp0)
led_controller_mcp1 = LEDController(mcp1, led_pins_mcp1)  # Falls es LEDs an mcp1 gibt

# Interrupt-Konfiguration nur für Taster-Pins
interrupt_enable_mcp0 = sum([1 << pin for pin in button_pins_mcp0])
interrupt_enable_mcp1 = sum([1 << pin for pin in button_pins_mcp1])

mcp0.interrupt_enable = interrupt_enable_mcp0
mcp0.interrupt_configuration = interrupt_enable_mcp0  # Interrupt nur bei Wertänderung auf default_value
mcp0.default_value = interrupt_enable_mcp0  # default_value auf HIGH (Pull-up)
mcp0.io_control = 0x44  # Interrupt als Open Drain und gespiegelt
mcp0.clear_ints()  # Interrupts initial löschen

mcp1.interrupt_enable = interrupt_enable_mcp1
mcp1.interrupt_configuration = interrupt_enable_mcp1  # Interrupt nur bei Wertänderung auf default_value
mcp1.default_value = interrupt_enable_mcp1  # default_value auf HIGH (Pull-up)
mcp1.io_control = 0x44  # Interrupt als Open Drain und gespiegelt
mcp1.clear_ints()  # Interrupts initial löschen

# GPIO-Setup für Interrupt-Pins
GPIO.setmode(GPIO.BCM)
interrupt_pin_mcp0 = 17  # Raspberry Pi Pin für Interrupt von mcp0
interrupt_pin_mcp1 = 27  # Raspberry Pi Pin für Interrupt von mcp1

GPIO.setup(interrupt_pin_mcp0, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(interrupt_pin_mcp1, GPIO.IN, GPIO.PUD_UP)

# Callback-Funktion für Interrupts
def handle_interrupt(channel):
    if channel == interrupt_pin_mcp0:
        for pin_flag in mcp0.int_flag:
            if pin_flag in button_pins_mcp0:
                print(f"Interrupt mcp0 - Pin: {pin_flag} geändert auf: {mcp0.get_pin(pin_flag).value}")
                led_controller_mcp0.toggle(button_pins_mcp0.index(pin_flag))
        mcp0.clear_ints()
    elif channel == interrupt_pin_mcp1:
        for pin_flag in mcp1.int_flag:
            if pin_flag in button_pins_mcp1:
                print(f"Interrupt mcp1 - Pin: {pin_flag} geändert auf: {mcp1.get_pin(pin_flag).value}")
                led_controller_mcp1.toggle(button_pins_mcp1.index(pin_flag))
        mcp1.clear_ints()

# GPIO Interrupts konfigurieren
try:
    GPIO.add_event_detect(interrupt_pin_mcp0, GPIO.FALLING, callback=handle_interrupt, bouncetime=10)
    GPIO.add_event_detect(interrupt_pin_mcp1, GPIO.FALLING, callback=handle_interrupt, bouncetime=10)
except RuntimeError as e:
    print(f"Fehler beim Einrichten der Interrupts: {e}")

# Hauptprogramm
try:
    print("Drücken Sie eine Taste, um einen Interrupt auszulösen.")
    while True:
        time.sleep(1)  # Main Loop

except KeyboardInterrupt:
    print("Programm beendet")
finally:
    GPIO.cleanup()
