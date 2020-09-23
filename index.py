from waitress import serve
import os
import pathlib
from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import numpy as np
import base64
import track

HOST = '0.0.0.0'    # on-board computer's IP address
# HOST = '132.148.137.212'    # on-board computer's IP address
PORT = 3000

ALLOWED_EXTENSIONS = set(['mov', 'avi', 'mp4'])

app = Flask(__name__)
app.secret_key = '658'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'templates/static/uploads'
app._static_folder = os.path.abspath("templates/static")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    out_file = ''
    if request.method == 'POST':
        if 'inFile' not in request.files:
            flash('No file part')
        file = request.files['inFile']
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            out_file = request.form['outFile']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            track.analysis_video(filename, out_file)
                
    return render_template('layouts/ui.html', out_file=out_file)

if __name__ == "__main__":
    serve(app, host=HOST, port=PORT)