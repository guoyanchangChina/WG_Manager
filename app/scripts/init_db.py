from app import create_app
import os,sqlite3
from ..extensions import bcrypt

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_default_admin(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE role='admin'")
    if cursor.fetchone() is None:
        password_hash = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (username, department, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (DEFAULT_USERNAME, "IT", password_hash, "admin"))
        conn.commit()
        print(f"[INFO] Default admin created: {DEFAULT_USERNAME} / {DEFAULT_PASSWORD}")
    else:
        print("[INFO] Admin user already exists.")

    conn.close()

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
        role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
        is_password_reset BOOLEAN DEFAULT FALSE
    );
''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            feature TEXT NOT NULL UNIQUE,
            ip_address TEXT NOT NULL UNIQUE,
            net_work TEXT NOT NULL,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            allowed_ips TEXT NOT NULL,       
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS net_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip_pool TEXT NOT NULL UNIQUE,
            gate_way TEXT NOT NULL,
            server_ip TEXT NOT NULL,         
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            listen_port INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        );
    ''')
    
    conn.commit()
    conn.close()


def main():
    app = create_app()

    print("Creating application context...")
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'xlyvpn.db')
        if not os.path.exists(db_path):
            print("Initializing database...")
            initialize_db()
            create_default_admin(db_path)
            print("Database initialized.")
        else:
            print("Database already exists.")

if __name__ == '__main__':
    main()
