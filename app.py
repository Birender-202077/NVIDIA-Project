from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
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

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df['PID'] = df['PID'].astype(str).str.strip()

    # Get preview data
    preview_data = df.head(5).to_dict('records')
    columns = df.columns.tolist()

    result = None
    if request.method == 'POST':
        pid = request.form.get('pid', '').strip()
        if pid:
            result = df[df['PID'] == pid].to_dict('records')
            if not result:
                flash(f'No details found for PID: {pid}', 'error')

    return render_template('search.html', 
                         filename=filename,
                         preview_data=preview_data,
                         columns=columns,
                         result=result[0] if result else None)

if __name__ == '__main__':
    app.run(debug=True)