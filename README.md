# psyonic-ble-tools

Psyonic Tools for communicating with the hand over BLE from a PC. 

Requirements:
- Linux PC with Bluetooth (or compatible dongle)
- Python 3.4 - 3.8 (tested with 3.6 & 3.8)
- Run install.sh to get required packages

To debug, run `bluetoothctl` in another terminal window to see Bluetooth discover and connection status live while the script runs. 

## Programs:

### `ble_cdump.py`

_This can be run with get_fs_dump.py_

This program connects to a hand (by name), gets the File System Dump (using command 'CDUMP'), and writes this to a file. This is used to record the state of each hand at a state in time, especially right before shipping to a customer. 

This may fail ~1/10 times due to the underlying bluetooth system being in a weird state. When this happens wait ~30 seconds and retry, it should work. 

### `ble_terminal.py`

This is a BLE terminal where you can view notifications from the hand and type commands to send to the hand. The mac address of the hand is required to connect. You may also need to run a scan from the command line to discover your device (`bluetoothctl` -> `scan on` -> wait a few seconds -> `scan off` -> `exit` -> `python3 ble_terminal.py`)