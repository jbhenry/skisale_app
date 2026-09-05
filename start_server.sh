#!/bin/bash
trap '' SIGINT
cd ~/skisale_app
source bin/activate
python serve.py

read -p "Press Enter to exit..."
