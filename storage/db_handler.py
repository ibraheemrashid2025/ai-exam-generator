# storage/db_handler.py
# Yeh file SQLite database ke saath kaam karti hai
# Har exam session save hota hai taake baad mein retrieve kar sako

import sqlite3
import json
import os
from datetime import datetime

# Database file ka path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sessions.db')

# ── Database Initialize ──────────────────────────────────────────────────────
# Pehli baar run hone par table banata hai
# Agar table already exist kare toh kuch nahi karta
def init_db():
    # Streamlit Cloud ke liye fix: Agar 'data' folder nahi hai toh khud bana lo
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            created_at TEXT NOT NULL,
            curriculum_output TEXT NOT NULL,
            questions_output TEXT NOT NULL,
            difficulty_output TEXT NOT NULL,
            rubric_output TEXT NOT NULL,
            analytics_output TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ── Save Session ─────────────────────────────────────────────────────────────
# Pipeline complete hone ke baad result save karta hai
# JSON dict ko string mein convert karke store karta hai
def save_session(session_name: str, pipeline_result: dict) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exam_sessions 
        (session_name, subject, created_at, curriculum_output, questions_output, 
         difficulty_output, rubric_output, analytics_output)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_name,
        pipeline_result['curriculum'].get('subject', 'Unknown'),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json.dumps(pipeline_result['curriculum']),
        json.dumps(pipeline_result['questions']),
        json.dumps(pipeline_result['difficulty']),
        json.dumps(pipeline_result['rubric']),
        json.dumps(pipeline_result['analytics'])
    ))
    session_id = cursor.lastrowid  # Naya record ka ID return karta hai
    conn.commit()
    conn.close()
    return session_id

# ── Get All Sessions ─────────────────────────────────────────────────────────
# Sidebar mein past sessions dikhane ke liye
def get_all_sessions() -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, session_name, subject, created_at 
        FROM exam_sessions 
        ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "session_name": r[1], "subject": r[2], "created_at": r[3]}
        for r in rows
    ]

# ── Get Single Session ───────────────────────────────────────────────────────
# Kisi specific session ka poora data load karta hai
def get_session_by_id(session_id: int) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "session_name": row[1],
        "subject": row[2],
        "created_at": row[3],
        "curriculum": json.loads(row[4]),
        "questions": json.loads(row[5]),
        "difficulty": json.loads(row[6]),
        "rubric": json.loads(row[7]),
        "analytics": json.loads(row[8])
    }

# ── Delete Session ───────────────────────────────────────────────────────────
# Kisi session ko delete karta hai
def delete_session(session_id: int) -> bool:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM exam_sessions WHERE id = ?', (session_id,))
    conn.commit()
    affected = cursor.rowcount  # Kitni rows delete huin
    conn.close()
    return affected > 0