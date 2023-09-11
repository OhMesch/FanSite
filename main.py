from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_required
from flask_login import login_user
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

from datetime import datetime
import os

app = Flask(__name__)
app.config.from_pyfile("flask_config.py")

login = LoginManager(app)
login.login_view = 'login'

class User(UserMixin):
    id = 'fan'
    password_hash = app.config['PASSWORD']

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User()

class LoginForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Adore Him')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User()
        if user.check_password(form.password.data):
            log(f'Login Approved')
            login_user(user)
            return redirect(url_for('index'))
        else:
            log('Login Failed')
            return redirect(url_for('login'))
            
    return render_template('login.html', title='Sign In', form=form)

@app.route('/')
@app.route('/index')
@login_required
def index():
    return send_from_directory('.', 'site.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    log(f"Received file upload request from {request.form['uuid']} for file {request.files['file'].filename}.")
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
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get-images')
@login_required
def get_images():
    # List all files in the UPLOAD_FOLDER
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return jsonify(files)

@app.route('/log', methods=['POST'])
@login_required
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