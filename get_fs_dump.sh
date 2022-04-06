#!/bin/bash

echo Running AENC Plotter
python3.9 $(dirname $(realpath $0))/ble_cdump.py
