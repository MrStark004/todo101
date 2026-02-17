import sqlite3

# Connect to a local file database (it will verify/create it automatically)
conn = sqlite3.connect("mydb.db", check_same_thread=False)
csr = conn.cursor()

# Create the table if it doesn't exist yet
csr.execute("""
    CREATE TABLE IF NOT EXISTS mytodos (
        todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_added TEXT,
        todo_title TEXT,
        todo_desc TEXT,
        todo_done BOOLEAN
    )
""")
conn.commit()