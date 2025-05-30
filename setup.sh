#!/bin/bash

set -e  # 出错即终止

PROJECT_DIR="/opt/wgmanager"
APP_NAME="wgmanager"
NGINX_CONF="/etc/nginx/sites-available/wgmanager"
NGINX_LINK="/etc/nginx/sites-enabled/wgmanager"
SOCK_PATH="/run/wgmanager/wgmanager.sock"
SUDOERS_FILE="/etc/sudoers.d/wgmanager"
SCRIPTS_DIR="$PROJECT_DIR/app/scripts"
ENV_FILE="$PROJECT_DIR/.env"
DEFAULT_USER="admin"
DEFAULT_PASSWORD="admin123"

info() {
    echo "[INFO] $1"
}

check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo "[ERROR] 请以 root 权限运行此脚本"
        exit 1
    fi
}

install_dependencies() {
    info "备份原有 sources.list"
    cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%F-%T)

    info "替换为清华镜像源..."
    UBUNTU_CODENAME=$(lsb_release -cs)
    cat > /etc/apt/sources.list <<EOF
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $UBUNTU_CODENAME main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $UBUNTU_CODENAME-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $UBUNTU_CODENAME-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $UBUNTU_CODENAME-security main restricted universe multiverse
EOF

    info "更新 apt 缓存..."
    apt update

    info "安装环境依赖..."
    apt install -y git python3 python3-pip python3-venv nginx wireguard gunicorn3
}

create_service_user() {
    info "创建系统用户 www-data"
    if ! getent passwd www-data >/dev/null; then
        adduser --system --group www-data
    else
        info "用户 www-data 已存在"
    fi
}

setup_project() {
    info "从 GitHub 克隆项目..."

    if [ -d "$PROJECT_DIR" ]; then
        info "项目目录已存在，清理旧目录..."
        rm -rf "$PROJECT_DIR"
    fi

    git clone git@github.com:guoyanchangChina/WG_Manager.git "$PROJECT_DIR"

    chown -R www-data:www-data "$PROJECT_DIR"
}

setup_venv() {
    info "配置 Python 虚拟环境..."
    cd "$PROJECT_DIR"
    sudo -u www-data python3 -m venv venv
    sudo -u www-data -H "$PROJECT_DIR/venv/bin/pip" install --no-cache-dir -r "$PROJECT_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
}

initialize_database() {
    info "初始化数据库..."
    sudo -u www-data $PROJECT_DIR/venv/bin/python "$PROJECT_DIR/init.py"
}

create_env_file() {
    info "初始化环境变量..."

    SERVER_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    WTF_CSRF_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    SERVER_PRIVATE_KEY=$(wg genkey)
    SERVER_PUBLIC_KEY=$(echo "$SERVER_PRIVATE_KEY" | wg pubkey)

    cat > "$ENV_FILE" <<EOF
# 环境变量配置
SERVER_PRIVATE_KEY="$SERVER_PRIVATE_KEY"
SERVER_PUBLIC_KEY="$SERVER_PUBLIC_KEY"
WTF_CSRF_SECRET_KEY="$WTF_CSRF_SECRET_KEY"
SERVER_SECRET_KEY="$SERVER_SECRET_KEY"
CONFIG_OUTPUT_DIR="$(realpath "$PROJECT_DIR/client-configs")"
EOF

    chown www-data:www-data "$ENV_FILE"
    info "环境变量配置成功！"
}

setup_nginx() {
    info "初始化 Nginx 反向代理..."
    cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://unix:$SOCK_PATH;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $PROJECT_DIR/static;
        expires 30d;
    }
}
EOF

    ln -sf "$NGINX_CONF" "$NGINX_LINK"
    nginx -t && systemctl reload nginx
    info "✅ Nginx 配置完成，服务已重新加载"
}

setup_sudoers() {
    info "配置用户权限，允许执行服务器脚本..."

    echo "www-data ALL=(ALL) NOPASSWD: /opt/wgmanager/venv/bin/python3 $SCRIPTS_DIR*" > "$SUDOERS_FILE"
    chmod 440 "$SUDOERS_FILE"
    info "sudoers 配置已写入 $SUDOERS_FILE"
}

setup_systemd() {
    info "注册系统服务..."
    cat > /etc/systemd/system/wgmanager.service <<EOF
[Unit]
Description=WG Manager - WireGuard Configuration Management Tool
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RuntimeDirectory=wgmanager
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 1 --bind unix:$SOCK_PATH wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable wgmanager
    systemctl start wgmanager
}

main() {
    check_root
    install_dependencies
    create_service_user
    setup_project
    create_env_file
    setup_venv
    initialize_database
    setup_sudoers
    setup_systemd
    setup_nginx
    info "🎉 WGManager 安装完成！"   
    PUBLIC_IP=$(curl -s ifconfig.me)
    info "你可以通过浏览器访问 http://$PUBLIC_IP"
    info "默认用户名: $DEFAULT_USER, 密码: $DEFAULT_PASSWORD"
}

main