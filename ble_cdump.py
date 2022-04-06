import BLE_GATT
from gi.repository import GLib
from threading import Thread
import time
import sys

#ubit_address = 'EF:79:55:E7:9C:48'
ubit_address = 'C3:1D:E5:62:35:B5'
uart_rx = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
uart_tx = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
count = 0
received = []
threshold = 0

def notify_handler(value):
    global count, received, threshold
    #print(f"Received: {bytes(value).decode('UTF-8')}")
    count = count+1
    received += value
    if count >= threshold:
      ubit.mainloop.quit()

def send_cdump():
    ubit.char_write(uart_rx, b'CDUMP\n')


ubit = BLE_GATT.Central(ubit_address)
ubit.connect()
ubit.on_value_change(uart_tx, notify_handler)

## First get the name
print("Getting Name")
threshold = 1
count = 0
ubit.char_write(uart_rx, bytes('RC\n'.format(message), 'utf-8'))
ubit.wait_for_notifications()

name = "{bytes(value).decode('UTF-8')}"
printf("Found name: " + name)
time.sleep(2)


# Next Get File System Dump
print("Getting File System Dump")
threshold = 128
count = 0
received = []
send_cdump()
ubit.wait_for_notifications()
ubit.cleanup()


# Validate and Write to File
if len(received) != 4068:
  print("Received: " + str(len(received)))
  sys.exit("Did not received required number of bytes")

fcontent = f"{bytes(totalfs)}"
fcontent = fcontent.replace("x","")
fcontent = fcontent[2:-1]
fname = "log-" + name + ".txt"
fp = open(fname, "x")
fp.write(fcontent)
fp.close()

print("Created file: " + fname)