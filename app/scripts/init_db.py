from app import create_app
import os,sqlite3
from dotenv import load_dotenv
from app.db import get_db  
from app import bcrypt

def initialize_db(db_path='instance/xlyvpn.db'):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
    );
''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            feature TEXT NOT NULL UNIQUE,
            ip_address TEXT NOT NULL UNIQUE,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        );
    ''')
    
    conn.commit()
    conn.close()

load_dotenv()

def create_super_user():
    username = "SuperUser"
    password = "000000"
    department = "IT"
    print("Creating application context...")
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
            print(f"✅ Super user '{username}' created.")
        except sqlite3.IntegrityError:
            print(f"❌ User '{username}' already exists.")

def main():
    app = create_app()
    print("Creating application context...")
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'xlyvpn.db')
        if not os.path.exists(db_path):
            print("Initializing database...")
            initialize_db()
            create_super_user()
            print("Database initialized.")
        else:
            print("Database already exists.")

if __name__ == '__main__':
    main()
