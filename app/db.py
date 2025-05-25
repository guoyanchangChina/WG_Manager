import sqlite3
from flask import current_app, g
import os



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

