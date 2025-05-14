import sqlite3
from flask import current_app, g

def initialize_db():
    conn = sqlite3.connect('instance/xlyvpn.db')
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get a connection to the SQLite DB and store it in Flask's g context."""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row  
    return g.db

def close_db(e=None):
    """Close the database connection (called automatically on app teardown)."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

