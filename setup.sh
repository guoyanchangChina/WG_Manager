#!/bin/bash

set -e  # 出错即终止

PROJECT_DIR="/opt/wgmanager"
APP_NAME="wgmanager"
NGINX_CONF="/etc/nginx/sites-available/wgmanager"
NGINX_LINK="/etc/nginx/sites-enabled/wgmanager"
SOCK_PATH="/run/wgmanager/wgmanager.sock"
SUDOERS_FILE="/etc/sudoers.d/wgmanager"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

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
    info "安装环境依赖..."
    apt update
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
    ENV_FILE="$PROJECT_DIR/.env"
    if [ -f "$ENV_FILE" ]; then
        info ".env 文件已存在，跳过创建"
        return
    fi

    info "创建默认 .env 文件..."

    cat > "$ENV_FILE" <<EOF
# 环境变量配置
SERVER_PUBLIC_KEY=your_server_public_key_here
SERVER_ENDPOINT=your_server_ip_or_domain:51820
CONFIG_OUTPUT_DIR=$PROJECT_DIR/client-configs
EOF

    chown www-data:www-data "$ENV_FILE"
    info ".env 文件已创建于 $ENV_FILE."
}

setup_nginx() {
    info "配置 Nginx 反向代理..."
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
    info "配置 sudo 权限，允许 www-data 无密码运行 script..."
    if [ ! -d "$SCRIPTS_DIR" ]; then
        mkdir -p "$SCRIPTS_DIR"
        chown root:root "$SCRIPTS_DIR"
        chmod 750 "$SCRIPTS_DIR"
    fi

    echo "www-data ALL=(ALL) NOPASSWD: /usr/bin/python3 $SCRIPTS_DIR/*" > "$SUDOERS_FILE"
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
}

main