import BLE_GATT
from gi.repository import GLib
from pydbus import SystemBus
import time
import sys


##### CONFIGURATION   ######
MAX_NUM_LOGS = 10
MAX_SCAN_TIME = 10
uart_rx = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
uart_tx = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'

#############################

##### DEFINES         ######
BLUEZ_SERVICE = 'org.bluez'
DEVICE_INTERFACE = 'org.bluez.Device1'
adapter_path = '/org/bluez/hci0'
#DEVICE_NAME = "21ABH058"
HAND_NAME_PREFIX = "PSYONIC"
NAME_LENGTH = 8

#############################


DEVICE_NAME = input("Input Hand Name (i.e. 21ABH058): \n")

if len(DEVICE_NAME) > NAME_LENGTH:
	sys.exit(f"\033[91mError: Device Name invalid, must be no more than " + str(NAME_LENGTH) + f" characters\033[0m")

print("Using Name: " + DEVICE_NAME)
print("---------------")


##### GLOBALS         ######
address = ""
bus = SystemBus()
adapter = bus.get('org.bluez', adapter_path)
mngr = bus.get('org.bluez', '/')
#############################

## Remove all known devices with Psyonic name, so we can find them on scan
def remove_psyonic_devices():
	global bus, adapter, mngr
	## Get all previously paired or recently seen (180 seconds?) devices
	mgr_objs = mngr.GetManagedObjects()
	for path in mgr_objs:
		if path.startswith(adapter_path + "/"): 		## If they are BLUEZ Devices Get Name
			name = mgr_objs[path].get(DEVICE_INTERFACE, {}).get('Alias')
			if name is None:
				pass
			elif name.startswith(HAND_NAME_PREFIX):  ## If they are Psyonic Names, remove
				adapter.RemoveDevice(path)

def stop_scan():
    try:
        adapter.StopDiscovery()
    except GLib.Error as err:
        pass
    mainloop.quit()
	
def on_device_found(device_path, device_props):
    global address
    name = device_props.get('Alias')
    if DEVICE_NAME in name:
        address = device_props.get('Address')
        stop_scan()

def on_iface_added(path, interfaces):
    if DEVICE_INTERFACE in interfaces:
        on_device_found(path, interfaces[DEVICE_INTERFACE])


## First, make sure discovery is off then remove all old bluetooth devices
try:
    adapter.StopDiscovery()
except GLib.Error as err:
    pass
print("Removing Old Psyonic Devices")
remove_psyonic_devices()

## Scan for devices until timeout or found
print("Scan for Device: \033[36m" + DEVICE_NAME + f"\033[0m")
mngr.onInterfacesAdded = on_iface_added
mainloop = GLib.MainLoop()
GLib.timeout_add_seconds(MAX_SCAN_TIME, stop_scan)
adapter.SetDiscoveryFilter({'DuplicateData': GLib.Variant.new_boolean(True)})
adapter.StartDiscovery()
mainloop.run()

## Exit if the address is still blank
if address == "":
	sys.exit(f"\033[91mError: Did not find address for device: \033[36m" + DEVICE_NAME + f"\033[0m")


print("Found Address: \033[36m" + address + f"\033[0m for: \033[36m" + DEVICE_NAME + f"\033[0m")
print(f"\033[32mSetup Complete\033[0m")
print("---------------")


count = 0
received = []
threshold = 0

def notify_handler(value):
    global count, received, threshold
    count = count+1
    received += value
    if count >= threshold:
      ubit.mainloop.quit()

## Create and connect
print("Attempting to connect...   " + address)
ubit = BLE_GATT.Central(address)
ubit.connect()
ubit.on_value_change(uart_tx, notify_handler)
print(f"\033[0m  Connection Successful\033[0m")
print("---------------")

## First get the name
print("Verifying Device Name")
threshold = 1
count = 0
ubit.char_write(uart_rx, b'RC\n')
ubit.wait_for_notifications()

name = f"{bytes(received[:8]).decode('UTF-8')}"
time.sleep(0.25)
print(f"  Found name: \033[36m" + name + f"\033[0m")
if not DEVICE_NAME in name:
	ubit.cleanup()
	sys.exit(f"\033[91mError: Device Name not a match\033[0m")
print("---------------")
time.sleep(1)  ## Delays so people can read what is on screen and verify

# Next Get File System Dump
threshold = 128
count = 0
received = []
print("Getting File System Dump")
ubit.char_write(uart_rx, b'CDUMP\n')
ubit.wait_for_notifications()
ubit.cleanup()

# Validate and Write to File
if len(received) != 4068:
  print("Received: " + str(len(received)))
  sys.exit(f"\033[91mError: Did not receive required number of bytes\033[0m")

print("Generating Log File")
fcontent = bytearray(received)
#fcontent = fcontent.replace("x","")
#fcontent = fcontent[2:-1]
fname = "log-" + name + ".txt"
createdFile = False
for i in range(0, 10):
  try:
    fp = open(fname, "xb")
    createdFile = True
    break;
  except: 
    fname = "log-" + name + "-" + str(i+1) + ".txt"

if createdFile:
  fp.write(fcontent)
  fp.close()
  print(f"\033[32mCreated file: " + fname)
else:
  sys.exit(f"\033[91mToo many log files already exist for: " + name)