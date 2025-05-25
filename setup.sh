#!/bin/bash

set -e  # 出错即终止

PROJECT_DIR="/opt/wgmanager"
APP_NAME="wgmanager"
NGINX_CONF="/etc/nginx/sites-available/wgmanager"
NGINX_LINK="/etc/nginx/sites-enabled/wgmanager"
SOCK_PATH="/run/wgmanager/wgmanager.sock"

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

setup_ssh_key() {
    SSH_DIR="/root/.ssh"
    KEY_NAME="id_rsa"
    PUB_KEY_PATH="$SSH_DIR/id_rsa.pub"
    PRIV_KEY_PATH="$SSH_DIR/id_rsa"

    info "配置 SSH 密钥..."

    if [ ! -d "$SSH_DIR" ]; then
        mkdir -p "$SSH_DIR"
        chmod 700 "$SSH_DIR"
    fi

    if [ -f "$PUB_KEY_PATH" ]; then
        info "SSH 密钥已存在，跳过生成步骤"
        return 0
    fi

    # 生成密钥
    ssh-keygen -t rsa -b 4096 -N "" -C "auto-deploy@wgmanager" -f "$SSH_DIR/$KEY_NAME"

    # 设置权限
    chmod 600 "$PRIV_KEY_PATH"
    chmod 644 "$PUB_KEY_PATH"

    # 输出公钥内容
    info "已生成公钥："
    cat "$PUB_KEY_PATH"

    info "请访问以下链接添加 SSH 密钥到 GitHub"
    info "https://github.com/settings/keys "

    # 等待用户完成操作
    read -p $'\n✅ 公钥已生成，请登录 GitHub 添加密钥后按 [Enter] 继续...'

    info "继续执行安装流程..."
}

check_github_ssh() {
    info "测试 GitHub SSH 连接..."

    ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"
    
    if [ $? -eq 0 ]; then
        info "GitHub SSH 认证成功"
    else
        echo "[ERROR] GitHub SSH 认证失败，请确认公钥已正确添加"
        exit 1
    fi
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
Environment="PATH=$PROJECT_DIR/venv/bin"
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
    setup_ssh_key
    check_github_ssh
    setup_project
    setup_venv
    initialize_database
    setup_systemd
    setup_nginx
    info "🎉 WGManager 安装完成！"   
    PUBLIC_IP=$(curl -s ifconfig.me)
    info "你可以通过浏览器访问 http://$PUBLIC_IP"
}

main