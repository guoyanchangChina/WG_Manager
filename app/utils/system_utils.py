from app.db import get_db
import socket
from contextlib import closing
import ipaddress

def get_next_available_port(start_port=51820, max_port=51900):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT listen_port FROM interfaces")
    used_ports = {row["listen_port"] for row in cursor.fetchall()}

    for port in range(start_port, max_port):
        if port in used_ports:
            continue
        # Check if port is free on the system
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port

    raise RuntimeError("No available ports found in the range.")

def get_next_available_subnet(prefix_len: int) -> str:
   
    base_network = ipaddress.IPv4Network("10.66.0.0/16")
    used_subnets = set()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT ip_address FROM interfaces")
    for row in cursor.fetchall():
        try:
            net = ipaddress.IPv4Interface(row["ip_address"]).network
            used_subnets.add(net)
        except ValueError:
            continue  

    for subnet in base_network.subnets(new_prefix=prefix_len):
        if subnet not in used_subnets:
            return f"{subnet.network_address}/{prefix_len}"

    raise RuntimeError(f"No available /{prefix_len} subnet left in 10.66.0.0/16")