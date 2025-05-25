import sys
import os

def add_peer(public_key, ip_address):
    server_config_path = "/etc/wireguard/wg0.conf"

    if os.geteuid() != 0:
        print("This script must be run as root.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(server_config_path, 'a') as f:
            f.write("\n[Peer]\n")
            f.write(f"PublicKey = {public_key}\n")
            f.write(f"AllowedIPs = {ip_address}/32\n")
        print("Peer added successfully.")
    except Exception as e:
        print(f"Error updating WireGuard config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: add_peer.py <public_key> <ip_address>", file=sys.stderr)
        sys.exit(1)

    public_key = sys.argv[1]
    ip_address = sys.argv[2]
    add_peer(public_key, ip_address)
