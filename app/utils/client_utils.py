import uuid
import ipaddress
import sqlite3
from app.db import get_db
from flask import g
from flask_login import current_user
import traceback
import subprocess
import os
def generate_feature():
    return uuid.uuid4().hex[:10]

def generate_ip_address(subnet_cidr: str):
    net = ipaddress.ip_network(subnet_cidr, strict=False)
    reserved = {str(net.network_address + 1)}  # e.g., 10.66.0.1

    db = g.db if hasattr(g, 'db') else get_db()
    cursor = db.cursor()
    cursor.execute("SELECT ip_address FROM clients")
    rows = cursor.fetchall()
    used_ips = {row[0].split('/')[0] for row in rows if row[0]}

    for ip in net.hosts():
        ip_str = str(ip)
        if ip_str not in reserved and ip_str not in used_ips:
            return f"{ip_str}/32"  # <-- Force /32 for client

    raise Exception("IP地址池耗尽，没有可用IP。")

def insert_with_retry(client_name, net_work, max_attempts=5):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT ip_pool FROM net_works WHERE name = ?", (net_work,))
    row = cursor.fetchone()
    if not row:
         raise Exception("未找到指定网络")

    subnet_cidr = row[0] 
    allowed_ips = subnet_cidr 
    print(f"Subnet CIDR: {subnet_cidr}, Allowed IPs: {allowed_ips}")

    for _ in range(max_attempts):
        feature = generate_feature()

        ip_address = generate_ip_address(subnet_cidr)
        
        try:
            cursor.execute("""
                INSERT INTO clients (name, feature, ip_address, net_work, private_key, public_key, allowed_ips, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_name,
                feature,
                ip_address,
                net_work,
                'temp_private',
                'temp_public',
                allowed_ips,
                current_user.username
            ))  
            db.commit()
            client_id = cursor.lastrowid
            return {
                'id': client_id,
                'feature': feature,
                'ip_address': ip_address
            }

        except sqlite3.IntegrityError as e:
            db.rollback()
            print(f"[Insert Attempt {_+1}] IntegrityError: {e}")
        except Exception as e:
            db.rollback()
            print(f"[Insert Attempt {_+1}] Unexpected Error: {e}")
            traceback.print_exc()

    raise Exception("写入数据库失败 at insert_with_retry（） 。")

def generate_keys():
    try:
        private_key = subprocess.check_output(['wg', 'genkey']).decode('utf-8').strip()
        
        public_key_process = subprocess.Popen(['wg', 'pubkey'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        public_key, _ = public_key_process.communicate(input=private_key.encode('utf-8'))
        public_key = public_key.decode('utf-8').strip()

        return {
            'private_key': private_key,
            'public_key': public_key
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Key generation failed: {e}")

def generate_client_config(client, private_key, public_key):
    config_dir = os.path.join(os.getcwd(), 'client_configs')
    os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, f"{client['feature']}.conf")
    with open(config_path, 'w',encoding='utf-8') as f:
        f.write(f"Client Name: {client['name']}\n")
        f.write(f"Client Feature: {client['feature']}\n")
        f.write(f"Client IP Address: {client['ip_address']}\n")
        f.write(f"Private Key: {private_key}\n")
        f.write(f"Public Key: {public_key}\n")
    return config_path

def delete_client(client_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    if not client:
        raise Exception("Client not found.")

    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    db.commit()

    # Placeholder for removing client from server config
    server_config_path = "/path/to/server/config.conf"
    with open(server_config_path, 'r') as f:
        lines = f.readlines()

    with open(server_config_path, 'w') as f:
        for line in lines:
            if str(client_id) not in line:
                f.write(line)