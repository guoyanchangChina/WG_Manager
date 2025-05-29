#!/usr/bin/env python3

import os
import sys
import subprocess

def generate_keypair():
    private_key = subprocess.check_output(["wg", "genkey"]).decode().strip()
    public_key = subprocess.check_output(["wg", "pubkey"], input=private_key.encode()).decode().strip()
    return private_key, public_key

def add_interface(interface_name, ip_address, listen_port):
    config_path = f"/etc/wireguard/{interface_name}.conf"

    if os.geteuid() != 0:
        sys.exit(1)

    private_key, public_key = generate_keypair()

    try:
        if os.path.exists(config_path):
            os.remove(config_path)

        with open(config_path, 'w') as f:
            f.write("[Interface]\n")
            f.write(f"Address = {ip_address}\n")
            f.write(f"PrivateKey = {private_key}\n")
            f.write(f"ListenPort = {listen_port}\n")
            f.write("SaveConfig = true\n")

        os.chmod(config_path, 0o600)
        subprocess.run(["wg-quick", "up", interface_name], check=True)
        print(private_key)
        print(public_key)

    except Exception as e:
        print(f"Error writing interface config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)

    interface_name = sys.argv[1]
    ip_address = sys.argv[2]
    listen_port = sys.argv[3]

    add_interface(interface_name, ip_address, listen_port)
