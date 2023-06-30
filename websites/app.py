from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from io import BytesIO
import matplotlib.pyplot as plt
import pyaudio
import wave

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chic_app.db'
db = SQLAlchemy(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Constants
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Global variables
frames = []

# Route to render the index page
@app.route('/')
def index():
    return redirect(url_for('register'))

def generate_audio():
    global frames

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    while True:
        data = stream.read(CHUNK_SIZE)
        frames.append(data)

        yield data

    stream.stop_stream()
    stream.close()
    p.terminate()

@app.route('/audio_feed')
def audio_feed():
    return Response(generate_audio(), mimetype='audio/x-wav')

# Define the DistressLog model
class DistressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Text)
    time = db.Column(db.Text)
    distress_level = db.Column(db.Text)
    duration = db.Column(db.REAL)
    phone_number = db.Column(db.Text)
    network_ssid = db.Column(db.Text)

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
            return render_template('history_logs.html', search_results=search_results, search_query=search_query,
                                   count=count)
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


# Helper function to generate the PDF report
def generate_pdf(history):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Define the header content
    logo_path = "static/logo.jpg"
    title = "CHIC REPORT"
    current_date = datetime.now().strftime("%Y-%m-%d")
    from_date = history[0].date
    to_date = history[-1].date
    header_y = 800
    separator_y = header_y - 160

    c.drawImage(logo_path, 50, header_y - 50, width=100, height=100)

    # Add text below the title
    text = "Recorded Logs from the Chic Device"
    c.setFont("Helvetica", 12)
    c.drawString(160, header_y - 15, text)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(160, header_y, title)
    c.setFont("Helvetica", 12)
    c.drawString(160, header_y - 25, f"from {from_date} to {to_date}")

    # Define the table content
    table_y = header_y - 160
    table_data = [
        ["Date", "Time", "Distress Level", "Duration", "Phone Number", "Network SSID"]
    ]
    for log in history:
        table_data.append([
            log.date,
            log.time,
            log.distress_level,
            str(log.duration),
            log.phone_number,
            log.network_ssid
        ])

    # Define the table style
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), 'red'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), 'beige'),
        ('GRID', (0, 0), (-1, -1), 1, 'black')
    ]

    # Draw the table
    c.setFont("Helvetica", 10)
    table = Table(table_data)
    table.setStyle(table_style)
    table.wrapOn(c, 800, 600)
    table.drawOn(c, 50, table_y)

    # Define the footer content
    footer_y = 50
    footer_text = f"This is a system-generated copy of the report for {current_date} from the Chic Device App."
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, footer_y, footer_text)

    c.save()

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# Route to download history logs as a PDF
@app.route('/download_history', methods=['POST'])
def download_history():
    # Retrieve the specified dates from the form
    from_date_str = request.form.get('from_date')
    to_date_str = request.form.get('to_date')

    # Convert the date strings to datetime objects
    from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
    to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

    # Get the history data based on the specified dates
    history = DistressLog.query.filter(DistressLog.date.between(from_date, to_date)).all()

    # Generate the PDF file
    generate_pdf(history)

    # Return the PDF file as a response for download
    return send_file('chic_report.pdf', as_attachment=True)


# Route to render the dashboard page after successful registration
@app.route('/dashboard')
def dashboard():
    latest_distress_log = DistressLog.query.order_by(DistressLog.id.desc()).first()
    registered_phone_number = latest_distress_log.phone_number if latest_distress_log else 'N/A'
    network_ssid = latest_distress_log.network_ssid if latest_distress_log else 'N/A'
    history_logs = DistressLog.query.order_by(DistressLog.id.desc()).all()

    logger.info("Registered Phone Number: %s", registered_phone_number)
    logger.info("Network Access: %s", network_ssid)

    return render_template('dashboard.html', registered_phone_number=registered_phone_number,
                           network_ssid=network_ssid, history_logs=history_logs)


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


# Route to render the audio analysis details page
@app.route('/audio_analysis_details')
def audio_analysis_details():
    return render_template('audio_analysis_details.html')




# Route to clear all logs from the database
@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    # Delete all DistressLog entries from the database
    DistressLog.query.delete()
    db.session.commit()

    # Redirect to the dashboard page after clearing the logs
    return redirect(url_for('history_logs'))
    
if __name__ == '__main__':
    app.run(debug=True)
