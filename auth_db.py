import sqlite3

# We changed the name to force a fresh start!
conn = sqlite3.connect("mytodos_pro.db", check_same_thread=False)
csr = conn.cursor()

# Create table with new columns for Date, Time, and Priority
csr.execute("""
    CREATE TABLE IF NOT EXISTS mytodos (
        todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_added TEXT,
        todo_title TEXT,
        todo_desc TEXT,
        todo_done BOOLEAN,
        due_date TEXT,
        due_time TEXT,
        priority TEXT
    )
""")

csr.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")

conn.commit()

def create_user(username, password):
    try:
        csr.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    csr.execute("SELECT password FROM users WHERE username = ?", (username,))
    data = csr.fetchone()
    if data and data[0] == password:
        return True
    return False