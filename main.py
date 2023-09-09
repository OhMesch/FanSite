from flask import Flask
from flask import jsonify
from flask import request
from flask import send_from_directory

from datetime import datetime
import os

app = Flask(__name__)

app.config.from_pyfile("flask_config.py")

@app.route('/')
def index():
    return send_from_directory('.', 'site.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    log(f"Recieved file upload request from {request.form['uuid']} for file {request.files['file'].filename}.")
    if isBanned(request.form['uuid']):
        log(f"Denied file upload request from {request.form['uuid']}. Reason: 'Is Banned'.")
        return jsonify({"error": "No file part"})
    if 'file' not in request.files:
        log(f"Denied file upload request from {request.form['uuid']}. Reason: 'No file part'.")
        return jsonify({"error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        log(f"Denied file upload request from {request.form['uuid']}. Reason: 'No selected file'.")
        return jsonify({"error": "No selected file"})
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        log(f"Accepted file upload request from {request.form['uuid']} for file {filename}.")
        return jsonify({"success": True})  

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get-images')
def get_images():
    # List all files in the UPLOAD_FOLDER
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return jsonify(files)

@app.route('/log/', methods=['POST'])
def log_data():
    logValue = request.form['message']
    if (logValue):
        log(logValue)
        return jsonify({"success": True})
    else:
        return jsonify({"error": "No message"})

def log(message):
    with(open(app.config['LOG_FILE'], 'a+')) as f:
        f.write(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}: {message}\n')

def isBanned(uuid):
    if not os.path.exists(app.config['SHADOW_BAN_FILE']):
        return False
    with(open(app.config['SHADOW_BAN_FILE'], 'r')) as f:
        for line in f:
            if uuid in line:
                return True
    return False

if __name__ == '__main__':
    log("Starting server...")
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        log(f"Created upload folder '{app.config['UPLOAD_FOLDER']}'")
    else:
        log(f"Using existing upload folder '{app.config['UPLOAD_FOLDER']}'")

    if not os.path.exists(app.config['SHADOW_BAN_FILE']):
        with(open(app.config['SHADOW_BAN_FILE'], 'w+')) as f:
            f.write('')
        log(f"Created shadow ban file '{app.config['SHADOW_BAN_FILE']}'")
    else:
        log(f"Using shadow ban file '{app.config['SHADOW_BAN_FILE']}'")
    app.run(debug=app.config['IS_DEBUG'], port=app.config['PORT'])