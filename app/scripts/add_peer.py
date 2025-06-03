import sys
import os

def add_peer(public_key, ip_address,network):
    server_config_path = f"/etc/wireguard/{network}.conf"
    if os.geteuid() != 0:
        print("This script must be run as root.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(server_config_path, 'a') as f:
            f.write("\n[Peer]\n")
            f.write(f"PublicKey = {public_key}\n")
            f.write(f"AllowedIPs = {ip_address}\n")
    except Exception as e:
        print(f"Error updating WireGuard config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: add_peer.py <public_key> <ip_address>", file=sys.stderr)
        sys.exit(1)

    public_key = sys.argv[1]
    ip_address = sys.argv[2]
    network = sys.argv[3]
    add_peer(public_key, ip_address, network)
