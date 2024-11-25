from flask import Flask, render_template, request, flash, redirect, url_for, session
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_key')


# Configure upload folder
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Path for metadata storage
FILE_METADATA = '/tmp/file_metadata.json'

def save_uploaded_file(filename):
    """Save the uploaded filename persistently."""
    with open(FILE_METADATA, 'w') as f:
        json.dump({'uploaded_file': filename}, f)

def get_uploaded_file():
    """Retrieve the uploaded filename."""
    if os.path.exists(FILE_METADATA):
        with open(FILE_METADATA, 'r') as f:
            data = json.load(f)
            return data.get('uploaded_file')
    return None
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home route displaying the role selection form."""
    if session.get('logged_in'):
        return render_template('index.html')  # Render the main content (dashboard) for logged-in users
    return render_template('base.html')

@app.route('/validate', methods=['POST'])
def validate():
    role = request.form.get('role')
    password = request.form.get('password')

    if role == 'admin' and password == 'abc':
        session['logged_in'] = True
        session['role'] = 'admin'  # Set the user's role
        return redirect(url_for('index'))  # Redirect to the dashboard

    elif role == 'user':
        session['logged_in'] = True
        session['role'] = 'user'  # Set the user's role

        filename = get_uploaded_file()
        if not filename:
            flash('No file uploaded by admin. Please contact admin.', 'error')
            return redirect(url_for('home'))
        return redirect(url_for('search', filename=filename)) 

    else:
        flash("Invalid role or password", 'error')
        return redirect(url_for('home'))  # Redirect back to login page

@app.route('/index', methods=['GET', 'POST'])
def index():
    print("Inside the /index route!")
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            save_uploaded_file(filename)
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('search', filename=filename))

        else:   
            flash('Invalid file type. Please upload an Excel file (.xlsx)', 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/search/<filename>', methods=['GET', 'POST'])
def search(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        flash('File not found. Please upload again.', 'error')
        return redirect(url_for('index'))

    # Read the uploaded Excel file using pandas
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df['PID'] = df['PID'].astype(str).str.strip()

    # Get preview data (first 5 rows)
    preview_data = df.head(5).to_dict('records')
    columns = df.columns.tolist()

    result = None
    if request.method == 'POST':
        pid = request.form.get('pid', '').strip()
        if pid:
            # Get all records for the entered PID
            result = df[df['PID'] == pid].to_dict('records')
            if not result:
                flash(f'No details found for PID: {pid}', 'error')

    return render_template('search.html', 
                         filename=filename,
                         preview_data=preview_data,
                         columns=columns,                  
                         result=result if result else None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove logged_in flag from session
    session.pop('role', None)  # Remove role from session
    flash("Logged out successfully", 'success')  # Optionally, flash a success message
    return redirect(url_for('home'))  # Redirect to the login page

if __name__ == '__main__':
    app.run(debug=True)
