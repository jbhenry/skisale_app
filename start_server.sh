#!/bin/bash
echo "==================================================="
echo " SkiSale App server is running."
echo " DO NOT CLOSE THIS WINDOW - it will stop the server."
echo " Press Ctrl-C to stop the server."
echo "==================================================="
echo ""

trap '' SIGINT
cd ~/skisale_app
source bin/activate
python serve.py

read -p "Press Enter to exit..."
