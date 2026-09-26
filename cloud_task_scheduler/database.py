import os
import sqlite3

DB_DIR = os.path.join(os.path.dirname(__file__), 'database')
DB_PATH = os.path.join(DB_DIR, 'scheduler.db')


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            role TEXT,
            status TEXT DEFAULT 'Active'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            owner TEXT,
            vm TEXT,
            priority TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduling_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT,
            total_tasks INTEGER,
            completed INTEGER,
            makespan REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS virtual_machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mips INTEGER NOT NULL,
            ram INTEGER NOT NULL,
            status TEXT DEFAULT 'Idle'
        )
        """
    )
    columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
    if 'password' not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT 'admin'")
    conn.execute(
        "INSERT OR IGNORE INTO users (username, email, role, status, password) VALUES (?, ?, ?, ?, ?)",
        ('admin', 'admin@cloudscheduler.com', 'Admin', 'Active', 'admin')
    )
    if conn.execute('SELECT COUNT(*) FROM virtual_machines').fetchone()[0] == 0:
        conn.executemany(
            'INSERT INTO virtual_machines (name, mips, ram, status) VALUES (?, ?, ?, ?)',
            [('Compute-01', 400, 512, 'Idle'), ('Compute-02', 520, 768, 'Idle'),
             ('Compute-03', 680, 1024, 'Idle'), ('Compute-04', 820, 1536, 'Idle')]
        )
    conn.commit()
    conn.close()
    return DB_PATH
