import os
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE_FILE = os.path.join(BASE_DIR, "papers.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR)

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            year INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_years():
    start = 2023
    current = datetime.now().year
    return list(range(current, start - 1, -1))

def get_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload-page")
def upload_page():
    return render_template("upload_page.html", years=get_years())

@app.route("/upload", methods=["POST"])
def handle_upload():
    subject = request.form.get("subject")
    exam_type = request.form.get("exam_type")
    year = request.form.get("year")
    file = request.files.get("file")

    if not file or file.filename == "":
        return "Error: No file uploaded."

    try:
        original_name = file.filename
        stored_name = f"{uuid.uuid4().hex}_{original_name}"
        save_path = os.path.join(UPLOAD_FOLDER, stored_name)

        file.save(save_path)

        conn = get_db()
        conn.execute('''
            INSERT INTO papers (subject, exam_type, year, original_filename, stored_filename)
            VALUES (?, ?, ?, ?, ?)
        ''', (subject, exam_type, int(year), original_name, stored_name))
        conn.commit()
        conn.close()

        return "<p>Upload successful.</p><a href='/'>Home</a>"

    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/search", methods=["GET"])
def search():
    subject = request.args.get("subject")
    exam_type = request.args.get("exam_type")
    year = request.args.get("year")

    results = []

    if request.args:
        conn = get_db()
        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        if subject:
            query += " AND subject = ?"
            params.append(subject)
        if exam_type:
            query += " AND exam_type = ?"
            params.append(exam_type)
        if year:
            query += " AND year = ?"
            params.append(int(year))

        query += " ORDER BY year DESC"
        results = conn.execute(query, params).fetchall()
        conn.close()

    return render_template("search.html", papers=results, years=get_years())

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)