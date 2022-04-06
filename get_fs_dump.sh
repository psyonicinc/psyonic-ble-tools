#!/bin/bash

echo Getting File System Dump
python3 $(dirname $(realpath $0))/ble_cdump.py

sleep inf
