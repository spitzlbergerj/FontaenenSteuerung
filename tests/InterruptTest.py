import signal
import sys
from gpiozero import Button

BUTTON_GPIO = 22

def signal_handler(sig, frame):
    print("\nExiting...")
    sys.exit(0)

def button_pressed_callback():
    print("Button pressed!")

if __name__ == '__main__':
    button = Button(BUTTON_GPIO, pull_up=True, bounce_time=0.1)
    
    button.when_pressed = button_pressed_callback
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()
