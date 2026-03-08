import sqlite3
from pathlib import Path

# Define database file location
DB_PATH = Path("db/study_os.db")


def get_connection():
    """
    Opens connection to database.
    If database does not exist, SQLite automatically creates it.
    """
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """
    Creates required tables if bthey don't already exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT,
            status TEXT DEFAULT 'Not Started'
        )

    """)
        # Table 2: Study Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            study_date TEXT,
            minutes INTEGER,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    """)
        # Table 3: Mastery Scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mastery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            score INTEGER,
            last_updated TEXT,
            next_review TEXT,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    """)
    conn.commit()
    conn.close()
