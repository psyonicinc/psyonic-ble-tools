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

# Next get some baseline battery readings

fname = 'batt-data.csv'
createdFile = False
for i in range(0,100):
	try: 
		fp=open(fname, 'w')
		createdFile = True;
		break;
	except:
		fmame = 'batt-data-' + str(i) + '.csv'

if not createdFile:
	sys.exit(f"\033[91mToo many log files already exist")
	
writer = csv.writer(fp)
headerRow = ["Timestamp", DEVICE_NAME + " Bat %")
writer.writerow(headerRow)
batteryRead = [-1,-1]
tstart = time.time()

def getBatt():
	threshold = 1
	count = 0
	received = []
	ubit.char_write(uart_rx, b'S0\n')
	ubit.wait_for_notifications()
	return received[4]
	
def writeBattRow():
	read = getBatt()
	batteryRead[0] = time.time() - tstart
	batteryRead[1] = read
	writer.writerow(batteryRead)
	
	
##Get some baseline readingss
print("Taking Baseline Readings...")
for i in range(0, 10):
	writeBattRow()
	time.sleep(1)
	print(str(i+1), end=" ")
	
print("\n---------------")
print("Measuring Battery During Various Grips")

ubit.char_write(uart_rx, b'g-1:0.75\n')

time.sleep(2)

print("Slow Power & Open")
writeBattRow()
ubit.char_write(uart_rx, b'g03:1\n')
for i in range(0,8):
	time.sleep(0.25)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g-1:1\n')
for i in range(0,8):
	time.sleep(0.25)
	writeBattRow()
	
print("Fast Power & Open")
for i in range(0,2):
	time.sleep(0.75)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g03:0.25\n')
for i in range(0,8):
	time.sleep(0.125)
	writeBattRow()

ubit.char_write(uart_rx, b'g-1:0.25\n')
for i in range(0,8):
	time.sleep(0.25)
	writeBattRow()
	
	
	print("Slow Power & Open")
writeBattRow()
ubit.char_write(uart_rx, b'g03:1\n')
for i in range(0,8):
	time.sleep(0.25)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g-1:1\n')
for i in range(0,8):
	time.sleep(0.25)
	writeBattRow()
	
print("Fast Pinch & Open")
for i in range(0,2):
	time.sleep(0.75)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g02:0.25\n')
for i in range(0,8):
	time.sleep(0.125)
	writeBattRow()

ubit.char_write(uart_rx, b'g-1:0.25\n')
for i in range(0,8):
	time.sleep(0.125)
	writeBattRow()


print("Fast Hang Loose & Open")
for i in range(0,2):
	time.sleep(0.75)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g17:0.25\n')
for i in range(0,8):
	time.sleep(0.125)
	writeBattRow()

ubit.char_write(uart_rx, b'g-1:0.25\n')
for i in range(0,8):
	time.sleep(0.125)
	writeBattRow()


print("Slow Hang Loose & Open")
for i in range(0,2):
	time.sleep(0.75)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g17:1.5\n')
for i in range(0,8):
	time.sleep(0.3)
	writeBattRow()

ubit.char_write(uart_rx, b'g-1:1.5\n')
for i in range(0,8):
	time.sleep(0.3)
	writeBattRow()

print("Waiting to baseline again")
for i in range(0, 10):
	writeBattRow()
	time.sleep(1)
	print(str(i+1), end=" ")
	
print("\n---------------")
print("Fast Finger Wave Readings")
ubit.char_write(uart_rx, b'g31:0.2\n')
for i in range(0,16):
	time.sleep(0.25)
	writeBattRow()
	
ubit.char_write(uart_rx, b'g08:1\n')
for i in range(0,4):
	time.sleep(0.75)
	writeBattRow()

print("Slow Finger Wave Readings")
ubit.char_write(uart_rx, b'g31:5\n')
for i in range(0,32):
	time.sleep(0.25)
	writeBattRow()

ubit.char_write(uart_rx, b'g08:1\n')
for i in range(0,4):
	time.sleep(0.75)
	writeBattRow()
	
print("Final Baseline Readings")
for i in range(0, 10):
	writeBattRow()
	time.sleep(1)
	print(str(i+1), end=" ")
	
print("\n---------------")

fp.close()
print(f"\033[32mCreated file: " + fname)