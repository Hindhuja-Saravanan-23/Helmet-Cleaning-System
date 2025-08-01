# Helmet Cleaning Automation System

A Raspberry Pi-based smart helmet cleaning kiosk featuring:

- Automated cleaning cycle (UV, heater, pump, exhaust fan)  
- Online payment (Razorpay integration)  
- Superadmin offline start mode  
- Wi-Fi management (scan & connect via UI)  
- Touchscreen-friendly fullscreen UI (Electron + Flask)  

## Features

- Flask backend controlling GPIO and cleaning logic  
- Razorpay integration for secure online payments  
- Superadmin login to start cleaning offline  
- Wi-Fi setup UI with SSID scanning  
- Animated UI for cleaning progress and success screens  
- Electron frontend for native fullscreen experience  
- Autostart on boot to behave like a standalone appliance  

## System Architecture

[Touchscreen UI] <-- Electron --> [Flask Server] <-- GPIO --> [Hardware Components]

markdown
Copy
Edit

- Electron: Displays the HTML UI in fullscreen kiosk mode  
- Flask: Handles routes, payments, and hardware control  
- RPi.GPIO: Controls UV, heater, pump, exhaust fan  
- Razorpay: Processes payments before starting the cleaning cycle  

## Hardware Requirements

- Raspberry Pi 3/4/5 with Raspbian  
- Relay module to control:
  - UV light + Door unlock  
  - Heater  
  - Water pump  
  - Exhaust fan  
- Door limit switch for safety  
- Touchscreen display  

## Project Structure
helmet_cleaner/
├── app.py # Flask backend (GPIO + logic)
├── templates/ # HTML UI pages
│ ├── splash.html
│ ├── index.html
│ ├── cleaning.html
│ └── ...
├── static/ # Images, CSS
├── helmet_cleaner_electron/ # Electron wrapper
│ ├── main.js
│ └── package.json
└── start_helmet_ui.sh # Startup script (Flask + Electron)
