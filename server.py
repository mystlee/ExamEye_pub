from flask import Flask, request, jsonify, send_file, make_response, render_template
import sqlite3
import os
import csv
import argparse
from datetime import datetime
from flask_cors import CORS
import zipfile
import secrets

app = Flask(__name__)
CORS(app)


PY_SCRIPT_TEMPLATE = "checker.py"
BATCH_SCRIPT_TEMPLATE = "monitor.bat"
REMOTE_WEB_IP_ADDRESS = "http://IP+port"

def short_time():
    return datetime.now().strftime("%y%m%d:%H%M%S")

def init_db(csv_path = None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT,
            password TEXT,
            subject_code TEXT,
            keyboard_log TEXT,
            clipboard_log TEXT,
            usb_log TEXT,
            bluetooth_log TEXT,
            tab_switch_log TEXT,
            critical_issue_log TEXT,
            last_login_time TEXT,
            last_login_ip TEXT,
            heartbeat_time TEXT,
            token TEXT,
            PRIMARY KEY (student_id, subject_code)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_log (
            student_id TEXT,
            subject_code TEXT,
            ip TEXT,
            timestamp TEXT
        )
    """)
    if csv_path and os.path.exists(csv_path):
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                sid = row['student_id']
                pwd = row['password']
                subj = row['subject_code']
                cursor.execute("SELECT * FROM students WHERE student_id=? AND subject_code=?", (sid, subj))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO students VALUES (?, ?, ?, '', '', '', '', '', '', '', '', '', '')
                    """, (sid, pwd, subj))
    conn.commit()
    conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    student_id = data.get("student_id")
    password = data.get("password")
    subject_code = data.get("subject_code")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id=? AND password=? AND subject_code=?",
                   (student_id, password, subject_code))
    user = cursor.fetchone()
    if user:
        ip_address = request.remote_addr
        login_time = short_time()
        token = secrets.token_hex(16)
        cursor.execute("""
            UPDATE students
            SET last_login_time=?, last_login_ip=?, token=?
            WHERE student_id=? AND subject_code=?
        """, (login_time, ip_address, token, student_id, subject_code))
        cursor.execute("INSERT INTO login_log VALUES (?, ?, ?, ?)",
                       (student_id, subject_code, ip_address, login_time))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "token": token})
    else:
        conn.close()
        return jsonify({"success": False}), 401

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    student_id = data.get("student_id")
    subject_code = data.get("subject_code")
    now = datetime.now().isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students SET heartbeat_time=? WHERE student_id=? AND subject_code=?
    """, (now, student_id, subject_code))
    conn.commit()
    conn.close()

    return jsonify({"status": "alive"})
    
@app.route("/download", methods=["GET"])
def download_script():
    student_id = request.args.get("student_id")
    subject_code = request.args.get("subject_code")
    folder_name = student_id
    os.makedirs(folder_name, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM students WHERE student_id=? AND subject_code=?", (student_id, subject_code))
    print(student_id, subject_code)
    token = cursor.fetchone()[0]
    print(cursor.fetchone())
    print(token)
    conn.close()

    with open(PY_SCRIPT_TEMPLATE, "r") as f:
        code = f.read()
    py_file_name = f"monitor_{student_id}_{subject_code}.py"
    py_file_path = os.path.join(folder_name, py_file_name)
    code = code.replace("__STUDENT_ID__", student_id).replace("__SUBJECT_CODE__", subject_code)
    code = code.replace("__REMOTE_SERVER__", REMOTE_WEB_IP_ADDRESS)
    code = code.replace("__TOKEN__", token)
    with open(py_file_path, "w") as f:
        f.write(code)

    with open(BATCH_SCRIPT_TEMPLATE, "r") as f:
        batch_template = f.read()
    batch_script = batch_template.replace("REM [MODIFY_HERE]", f"py.exe {py_file_name}")
    bat_file_path = os.path.join(folder_name, "monitor.bat")
    with open(bat_file_path, "w") as f:
        f.write(batch_script)


    zip_name = f"{student_id}.zip"
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        zipf.write(py_file_path, arcname=os.path.join(folder_name, py_file_name))
        zipf.write(bat_file_path, arcname=os.path.join(folder_name, "monitor.bat"))

    def cleanup():
        os.remove(py_file_path)
        os.remove(bat_file_path)
        os.rmdir(folder_name)
        os.remove(zip_name)

    response = make_response(send_file(zip_name, as_attachment=True))
    response.call_on_close(cleanup)

    return response

@app.route("/log_event", methods=["POST"])
def log_event():
    data = request.get_json()
    student_id = data.get("student_id")
    subject_code = data.get("subject_code")
    token = data.get("token")
    log_type = data.get("log_type")
    content = data.get("content")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM students WHERE student_id=? AND subject_code=?",
                   (student_id, subject_code))
    stored_token = cursor.fetchone()
    if not stored_token or stored_token[0] != token:
        conn.close()
        return jsonify({"status": "unauthorized"}), 403

    column_map = {
        "keyboard": "keyboard_log",
        "clipboard": "clipboard_log",
        "usb": "usb_log",
        "bluetooth": "bluetooth_log",
        "tab": "tab_switch_log",
        "critical": "critical_issue_log"
    }

    column = column_map.get(log_type)
    if not column:
        return jsonify({"status": "invalid log type"}), 400

    cursor.execute(f"SELECT {column} FROM students WHERE student_id=? AND subject_code=?",
                   (student_id, subject_code))
    current_log = cursor.fetchone()
    updated_log = (current_log[0] + "\n" if current_log[0] else "") + f"[{short_time()}] {content}"
    cursor.execute(f"UPDATE students SET {column}=? WHERE student_id=? AND subject_code=?",
                   (updated_log, student_id, subject_code))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help = "student list(.csv)", required = True)
    parser.add_argument("--db", help = "DB path(.csv)", required = True)
    parser.add_argument("--port", help = "port", required = True)
    args = parser.parse_args()
    DB_FILE = args.db
    init_db(args.csv)
    app.run(host = "0.0.0.0", port = args.port)
