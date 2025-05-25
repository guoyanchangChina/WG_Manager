from app import create_app, bcrypt
from app.db import get_db  
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

def create_admin_user(username, password, department='IT'):
 
    app = create_app()
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, department, role)
                VALUES (?, ?, ?, 'admin')
            ''', (username, password_hash, department))
            db.commit()
            print(f"✅ Admin user '{username}' created.")
        except sqlite3.IntegrityError:
            print(f"❌ User '{username}' already exists.")

if __name__ == '__main__':
    create_admin_user('admin', '000000', '电气')
