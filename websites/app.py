from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import pyaudio
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chic_app.db'
db = SQLAlchemy(app)
audio_data = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Constants for audio settings
CHUNK_SIZE = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

pa = pyaudio.PyAudio()
stream = pa.open(format=FORMAT,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 frames_per_buffer=CHUNK_SIZE)

# Define the DistressLog model
class DistressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Text)
    time = db.Column(db.Text)
    distress_level = db.Column(db.Text)
    duration = db.Column(db.REAL)
    phone_number = db.Column(db.Text)
    network_ssid = db.Column(db.Text)


# Route to render the index page
@app.route('/')
def index():
    return redirect(url_for('register'))


# Route to render the History page after clicking the View All Logs button
@app.route('/history_logs', methods=['GET', 'POST'])
def history_logs():
    # Get the search query from the form submission
    search_query = request.form.get('query')

    if search_query:
        # Perform the search operation in your database using the 'search_query' variable
        search_results = DistressLog.query.filter(
            (DistressLog.distress_level.ilike(f'%{search_query}%')) |
            (DistressLog.duration.ilike(f'%{search_query}%')) |
            (DistressLog.phone_number.ilike(f'%{search_query}%')) |
            (DistressLog.time.ilike(f'%{search_query}%')) |
            (DistressLog.date.ilike(f'%{search_query}%'))
        ).all()
        count = len(search_results)

        if count > 0:
            # Display search results if any
            return render_template('history_logs.html', search_results=search_results, search_query=search_query, count=count)
        else:
            # Display "No Search Found" message
            return render_template('history_logs.html', no_results=True, search_query=search_query)
    else:
        # Fetch all history logs from the database
        history_logs = DistressLog.query.order_by(DistressLog.id.desc()).all()
        return render_template('history_logs.html', history_logs=history_logs)


# Route to delete each log in the History Logs page
@app.route('/delete_log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    log = DistressLog.query.get(log_id)
    if log:
        db.session.delete(log)
        db.session.commit()
    return redirect(url_for('history_logs'))


# Route to render the dashboard page after successful registration
@app.route('/dashboard')
def dashboard():
    latest_distress_log = DistressLog.query.order_by(DistressLog.id.desc()).first()
    registered_phone_number = latest_distress_log.phone_number if latest_distress_log else 'N/A'
    network_ssid = latest_distress_log.network_ssid if latest_distress_log else 'N/A'
    history_logs = DistressLog.query.order_by(DistressLog.id.desc()).all()

    logger.info("Registered Phone Number: %s", registered_phone_number)
    logger.info("Network Access: %s", network_ssid)

    # Fetch all history logs from the database
    history_logs = DistressLog.query.order_by(DistressLog.id.desc()).all()

    return render_template('dashboard.html', registered_phone_number=registered_phone_number, network_ssid=network_ssid, history_logs=history_logs)


# Route to handle the device control
@app.route('/toggle-device', methods=['POST'])
def toggle_device():
    # Get the state of the toggle button from the request
    device_state = request.form.get('device_state')

    if device_state == 'on':
        # Call the function to turn on the IoT device
        turn_on_device()
        # Add device control logic here
        pass
    elif device_state == 'off':
        # Call the function to turn off the IoT device
        turn_off_device()
        # Add device control logic here
        pass

    # Return a response indicating the success or failure of the device control
    return 'Device state updated successfully'


# Route to render the register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the phone number from the form data
        network_ssid = request.form.get('network_ssid')
        phone_number = request.form.get('phone_number')

        # Create a new DistressLog instance and save it to the database
        distress_log = DistressLog(
            date=datetime.now().date().isoformat(),
            time=datetime.now().time().isoformat(),
            distress_level='Mildly Distressed',  # prediction of the model should be here
            duration=0.0,
            phone_number=phone_number,  # Save the phone number to the database
            network_ssid=network_ssid  # Save the network SSID to the database
        )
        db.session.add(distress_log)
        db.session.commit()

        # Redirect to the dashboard page after successful registration
        return redirect(url_for('dashboard'))

    # If it's a GET request, simply render the register page
    return render_template('register.html')


# Route to clear all logs from the database
@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    # Delete all DistressLog entries from the database
    DistressLog.query.delete()
    db.session.commit()

    # Redirect to the dashboard page after clearing the logs
    return redirect(url_for('history_logs'))


# Route to handle the start button click
@app.route('/start-button', methods=['POST'])
def start_button():
    global audio_data
    audio_data = []

    def callback(in_data, frame_count, time_info, status):
        audio_data.extend(np.frombuffer(in_data, dtype=np.float32))
        return None, pyaudio.paContinue

    stream.start_stream(callback=callback)
    return 'Audio processing started'


# Route to handle the end button click
@app.route('/end-button', methods=['POST'])
def end_button():
    global audio_data
    stream.stop_stream()
    audio_data = np.array(audio_data)
    return 'Audio processing ended'


# Route to handle the audio data request
@app.route('/get-audio-data')
def get_audio_data():
    global audio_data
    if audio_data is None:
        return jsonify({'audio_data': []})
    else:
        return jsonify({'audio_data': audio_data.tolist()})


if __name__ == '__main__':
    app.run(debug=True)
