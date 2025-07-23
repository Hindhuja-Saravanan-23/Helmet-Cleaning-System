from flask import Flask, render_template, request, redirect, jsonify, session
import razorpay
import hmac
import hashlib
import subprocess
import threading
import time
import RPi.GPIO as GPIO
import atexit
import os
import json

app = Flask(__name__)
app.secret_key = "some_random_secret_key"

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

COMBINED_OUTPUT_PIN = 6  # UV + Door Unlock
HEATER_PIN = 12
PUMP_PIN = 13
EXHAUST_FAN_PIN = 19
DOOR_LIMIT_SWITCH_PIN = 27

output_pins = [COMBINED_OUTPUT_PIN, HEATER_PIN, PUMP_PIN, EXHAUST_FAN_PIN]
for pin in output_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

GPIO.setup(DOOR_LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

RAZORPAY_KEY_ID = 'rzp_test_ZejwPCxlGLqR73'
RAZORPAY_KEY_SECRET = 'tdZDCoEhr4PNH6pOCimGWKKA'

DOOR_CLOSE_TIMEOUT = 120
SUPERADMIN_PASSWORD = "admin123"
wifi_verified = False

process_status = {
    "complete": False,
    "waiting_manual_start": False,
    "in_progress": False,
    "error": ""
}

def is_door_closed():
    return GPIO.input(DOOR_LIMIT_SWITCH_PIN) == GPIO.HIGH

def is_wifi_connected():
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'WIFI', 'g'], capture_output=True, text=True)
        return "enabled" in result.stdout and subprocess.run(
            ['nmcli', '-t', '-f', 'DEVICE,STATE', 'd'], capture_output=True, text=True
        ).stdout.find("connected") != -1
    except:
        return False

@atexit.register
def cleanup():
    for pin in output_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()

def notify_user(msg):
    print("NOTIFICATION:", msg)

def cleaning_sequence():
    print("Helmet cleaning process started")
    process_status.update({
        "complete": False,
        "waiting_manual_start": False,
        "in_progress": True,
        "error": ""
    })

    print(" Turning on UV Light + Door Unlock (combined)")
    GPIO.output(COMBINED_OUTPUT_PIN, GPIO.HIGH)

    def pump_on_then_heater():
        time.sleep(5)
        print("Turning on Pump")
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        time.sleep(40)
        print(" Turning on Heater (after 40s of pump ON)")
        GPIO.output(HEATER_PIN, GPIO.HIGH)

    def combined_off():
        time.sleep(360)
        print("Turning off UV + Door Unlock (combined)")
        GPIO.output(COMBINED_OUTPUT_PIN, GPIO.LOW)

    def heater_off():
        time.sleep(345)
        print("Turning off Heater")
        GPIO.output(HEATER_PIN, GPIO.LOW)

    def pump_to_exhaust():
        time.sleep(240)
        print("Turning off Pump, turning on Exhaust Fan")
        GPIO.output(PUMP_PIN, GPIO.LOW)
        GPIO.output(EXHAUST_FAN_PIN, GPIO.HIGH)
        time.sleep(120)
        print("Turning off Exhaust Fan")
        GPIO.output(EXHAUST_FAN_PIN, GPIO.LOW)

    def mark_complete():
        time.sleep(370)
        process_status.update({
            "complete": True,
            "in_progress": False,
            "waiting_manual_start": False
        })
        print("Helmet cleaning complete.")
        notify_user("Helmet cleaning complete.")

    threading.Thread(target=pump_on_then_heater).start()
    threading.Thread(target=combined_off).start()
    threading.Thread(target=heater_off).start()
    threading.Thread(target=pump_to_exhaust).start()
    threading.Thread(target=mark_complete).start()

@app.route('/live-status')
def live_status():
    status = {
        "combined_uv_door": GPIO.input(COMBINED_OUTPUT_PIN),
        "heater": GPIO.input(HEATER_PIN),
        "pump": GPIO.input(PUMP_PIN),
        "exhaust_fan": GPIO.input(EXHAUST_FAN_PIN),
        "door_closed": is_door_closed()
    }
    return jsonify(status)

@app.route('/')
def splash():
    process_status.update({
        "waiting_manual_start": False,
        "in_progress": False,
        "complete": False,
        "error": ""
    })
    session.pop("superadmin_logged_in", None)
    return render_template('splash.html')

@app.route('/splash')
def splash_alias():
    return render_template('splash.html')

@app.route('/home')
def home():
    global wifi_verified
    if not wifi_verified:
        if is_wifi_connected():
            wifi_verified = True
    session.pop("superadmin_logged_in", None)
    return render_template('index.html')

@app.route('/start_after_superadmin')
def start_after_superadmin():
    if session.get("superadmin_logged_in"):
        process_status["waiting_manual_start"] = True
        return render_template('start_after_superadmin.html')
    return redirect('/home')

@app.route('/start_after_payment')
def start_after_payment():
    return render_template('start_after_payment.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/create-order', methods=['POST', 'GET'])
def create_order():
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order = client.order.create({
            'amount': 100 * 100,
            'currency': 'INR',
            'receipt': 'receipt_fixed_100',
            'payment_capture': 1
        })
        return render_template('pay.html', key_id=RAZORPAY_KEY_ID, order=order, amount=100)
    except Exception as e:
        print(" Razorpay create_order() failed:", e)
        return render_template("error.html", message=f"create order failed: {str(e)}"), 500

@app.route('/payment-verification', methods=['POST'])
def payment_verification():
    try:
        data = request.form
        order_id = data['razorpay_order_id']
        payment_id = data['razorpay_payment_id']
        signature = data['razorpay_signature']

        generated_sig = hmac.new(
            bytes(RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(order_id + "|" + payment_id, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_sig != signature:
            return "Invalid signature", 400

        notify_user(" Payment successful.")
        process_status.update({"waiting_manual_start": True, "error": ""})
        return redirect('/start_after_payment')

    except Exception as e:
        process_status["error"] = str(e)
        return f"Verification error: {str(e)}", 400

@app.route('/manual-start', methods=['POST'])
def manual_start():
    if not process_status["waiting_manual_start"]:
        return " Not allowed right now."

    notify_user("Auto-start triggered. Waiting for door close...")
    start = time.time()
    while not is_door_closed():
        if time.time() - start > DOOR_CLOSE_TIMEOUT:
            notify_user("Timeout.")
            process_status.update({"waiting_manual_start": False, "error": "Door not closed in time"})
            return redirect('/error')
        time.sleep(1)

    notify_user("🚪 Door closed. Starting cleaning.")
    cleaning_sequence()
    return redirect('/cleaning')

@app.route('/superadmin-login', methods=['POST'])
def superadmin_login():
    password = request.form.get("password", "")
    if password == SUPERADMIN_PASSWORD:
        session['superadmin_logged_in'] = True
        return jsonify({"status": "success", "message": "Superadmin logged in."})
    return jsonify({"status": "error", "message": "Incorrect password."}), 403

@app.route('/offline-start', methods=['POST'])
def offline_start():
    if not session.get("superadmin_logged_in"):
        return "Superadmin not logged in.", 403
    process_status.update({"waiting_manual_start": True, "error": ""})
    return redirect('/start_after_superadmin')

@app.route('/cleaning')
def cleaning():
    return render_template('cleaning.html', duration=370)

@app.route('/complete')
def complete():
    return render_template('complete.html')

@app.route('/error')
def error():
    try:
        with open("error_log.txt", "r") as f:
            message = f.read().strip()
    except:
        message = "❌ Unknown failure occurred."
    return render_template('error.html', message=message)

@app.route('/log-error', methods=['POST'])
def log_error():
    reason = request.json.get("reason", "Unknown error")
    with open("error_log.txt", "w") as f:
        f.write(reason)
    return jsonify({"status": "logged"})

@app.route('/wifi')
def wifi_page():
    return render_template('wifi.html')

@app.route('/wifi-scan')
def wifi_scan():
    subprocess.run(["nmcli", "dev", "wifi", "rescan"], capture_output=True)
    time.sleep(2)
    result = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], capture_output=True, text=True)
    networks = list(filter(None, set(result.stdout.strip().split('\n'))))
    return {"networks": networks}

@app.route('/wifi-connect', methods=['POST'])
def wifi_connect():
    global wifi_verified
    ssid = request.form.get("ssid")
    password = request.form.get("password")
    result = subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], capture_output=True, text=True)
    if result.returncode == 0:
        wifi_verified = True
        return redirect('/home')
    else:
        return f"❌ Failed: {result.stderr}", 500

if __name__ == '__main__':
    print("Flask app starting...")
    app.run(host='0.0.0.0', port=5000)
