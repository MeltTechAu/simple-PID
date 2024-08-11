import time
import board
import digitalio
import adafruit_max31855
import RPi.GPIO as GPIO
from simple_pid import PID
from flask import Flask, render_template, request, jsonify
from threading import Thread
import logging
import signal
import sys

# Configuration for SPI and GPIO
RELAY_PIN = 20

try:
    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.LOW)

    # Initialize SPI and MAX31855 sensor
    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D8)
    sensor = adafruit_max31855.MAX31855(spi, cs)

except Exception as e:
    logging.error(f"Initialization error: {e}")
    raise SystemExit("Failed to initialize hardware. Ensure all connections are correct and retry.")

# Initialize Flask app
app = Flask(__name__)

# PID parameters
pid = PID(1, 0.1, 0.05, setpoint=0)
pid.output_limits = (0, 1)  # PID output will be between 0 and 1

# Global variables
current_temperature = 0
set_point = 0
hold_time = 0
start_time = None
kiln_running = False
last_valid_temperature = None  # Global variable to store the last valid temperature
last_loop_time = time.time()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

def get_temperature():
    global last_valid_temperature
    try:
        temp = sensor.temperature  # Read the temperature directly
        logging.debug(f"Reading Temperature: {temp} °C")
        
        if temp is not None:
            last_valid_temperature = temp  # Update the last valid temperature
            return temp
        else:
            raise RuntimeError('Failed to read temperature')
    except Exception as e:
        logging.error(f"Error reading temperature: {e}")
        return last_valid_temperature  # Return the last valid temperature in case of an error

def control_kiln(output):
    try:
        if output >= 0.5:
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            logging.debug("Relay turned ON")
        else:
            GPIO.output(RELAY_PIN, GPIO.LOW)
            logging.debug("Relay turned OFF")
    except Exception as e:
        logging.error(f"Error controlling kiln: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_kiln():
    global set_point, hold_time, start_time, kiln_running
    try:
        data = request.get_json()
        set_point = float(data['set_point'])
        hold_time = int(data['hold_time'])
        pid.setpoint = set_point
        start_time = time.time()
        kiln_running = True
        logging.info(f"Kiln started with set point: {set_point}°C, hold time: {hold_time} seconds")
        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Error starting kiln: {e}")
        return jsonify(success=False)

@app.route('/stop', methods=['POST'])
def stop_kiln():
    global kiln_running
    try:
        kiln_running = False
        GPIO.output(RELAY_PIN, GPIO.LOW)
        logging.info("Kiln stopped")
        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Error stopping kiln: {e}")
        return jsonify(success=False)

@app.route('/status', methods=['GET'])
def status():
    global current_temperature
    try:
        current_temperature = get_temperature()
        elapsed_time = time.time() - start_time if start_time else 0
        return jsonify(current_temperature=current_temperature, set_point=set_point, elapsed_time=elapsed_time)
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return jsonify(success=False)

def control_loop():
    global current_temperature, kiln_running, last_loop_time
    while True:
        try:
            if kiln_running:
                current_temperature = get_temperature()
                if current_temperature is not None:
                    output = pid(current_temperature)
                    control_kiln(output)
                    logging.debug(f"Control loop output: {output}")
                else:
                    logging.error("Current temperature is None, stopping kiln")
                    kiln_running = False
                    GPIO.output(RELAY_PIN, GPIO.LOW)
            else:
                GPIO.output(RELAY_PIN, GPIO.LOW)
            
            # Check for safety timeout
            if time.time() - last_loop_time > 10:
                logging.error("Control loop timeout, stopping kiln")
                kiln_running = False
                GPIO.output(RELAY_PIN, GPIO.LOW)
            
            last_loop_time = time.time()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in control loop: {e}")

def handle_exit(sig, frame):
    logging.info("Shutting down...")
    global kiln_running
    kiln_running = False
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == '__main__':
    control_thread = Thread(target=control_loop)
    control_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logging.error(f"Error running Flask app: {e}")
        raise SystemExit("Failed to start the Flask app.")
