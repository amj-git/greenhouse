#!/bin/bash

#run on local display
export DISPLAY=:0.0

#Select the Python virtual environment where Kivy and dependencies were installed
source /home/pi/kivy/.venv/bin/activate

#Start the pigpio daemon
sudo pigpiod

#Start the greenhouse app
cd  /home/pi/greenhouse
python3 gh_gui.py
