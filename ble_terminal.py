import BLE_GATT
from gi.repository import GLib
from threading import Thread
import re
import sys

uart_rx = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
uart_tx = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'

mac_addr = input("Input Mac Addr (i.e. C3:1D:E5:62:35:B5): \n")

if re.match(r'^[a-fA-F0-9]{2}(:[a-fA-F0-9]{2}){5}\Z', mac_addr) is None:
	sys.exit(mac_addr + " is not a valid mac addr")

print("Attempting to connect to: " + mac_addr)
ubit = BLE_GATT.Central(mac_addr)
ubit.connect()

def notify_handler(value):
    try:
        print(f"Received: {bytes(value).decode('UTF-8')}")
    except: 
        print(f"Received (binary): 0x" + bytes(value).hex())


def input_thread():
	while(1):
		message = input()
		if(message.lower() == "exit"):
			print("Exiting...")
			ubit.cleanup()
			return
		print("Sending: " + str(message))
		ubit.char_write(uart_rx, bytes('{}\n'.format(message), 'utf-8'))


print("Connected!")
ubit.on_value_change(uart_tx, notify_handler)
t1 = Thread(target=input_thread)
t1.start()
print("Type your commands, followed by enter. Use 'exit' to end this program")
ubit.wait_for_notifications()

t1.join()

