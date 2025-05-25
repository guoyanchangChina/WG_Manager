#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/wgmanager/.env")

CONFIG_DIR = os.getenv("CONFIG_OUTPUT_DIR", "/opt/wgmanager/client-configs")
SERVER_PUBLIC_KEY = os.getenv("SERVER_PUBLIC_KEY")
SERVER_ENDPOINT = os.getenv("SERVER_ENDPOINT", "vpn.example.com:51820")
ALLOWED_IPS = "0.0.0.0/0"

def generate_client_config(feature, private_key, ip_address):
    if not SERVER_PUBLIC_KEY:
        print("SERVER_PUBLIC_KEY is not set in .env", file=sys.stderr)
        sys.exit(1)

    client_config = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_address}/24
DNS = 8.8.8.8

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_ENDPOINT}
AllowedIPs = {ALLOWED_IPS}
PersistentKeepalive = 25
"""

    os.makedirs(CONFIG_DIR, exist_ok=True)

    output_path = os.path.join(CONFIG_DIR, f"{feature}.conf")
    try:
        with open(output_path, 'w') as f:
            f.write(client_config)
        print(output_path)
    except Exception as e:
        print(f"Error writing config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: generate_client_config.py <feature> <private_key> <ip_address>", file=sys.stderr)
        sys.exit(1)

    feature = sys.argv[1]
    private_key = sys.argv[2]
    ip_address = sys.argv[3]
    generate_client_config(feature, private_key, ip_address)
