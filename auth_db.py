import sqlite3

conn = sqlite3.connect("mytodos.db", check_same_thread=False)
csr = conn.cursor()

# Table 1: Todos (Same as before)
csr.execute("""
    CREATE TABLE IF NOT EXISTS mytodos (
        todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_added TEXT,
        todo_title TEXT,
        todo_desc TEXT,
        todo_done BOOLEAN
    )
""")

# Table 2: Users (New!)
csr.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")

conn.commit()

# Helper function to check if user exists
def create_user(username, password):
    try:
        csr.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username already taken

def verify_user(username, password):
    csr.execute("SELECT password FROM users WHERE username = ?", (username,))
    data = csr.fetchone()
    if data and data[0] == password:
        return True
    return False