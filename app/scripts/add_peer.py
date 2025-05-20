import sys

def add_peer(public_key, ip_address):
    server_config_path = "/etc/wireguard/wg0.conf"  # 你的 wg 配置文件路径
    with open(server_config_path, 'a') as f:
        f.write("\n[Peer]\n")
        f.write(f"PublicKey = {public_key}\n")
        f.write(f"AllowedIPs = {ip_address}/32\n")
    print("Peer added successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: add_peer.py <public_key> <ip_address>")
        sys.exit(1)

    public_key = sys.argv[1]
    ip_address = sys.argv[2]
    add_peer(public_key, ip_address)
