from flask import Blueprint,Response
from flask import render_template, flash, redirect, url_for, request
from ..db import get_db
from ..forms import AddClientForm,EmptyForm
from ..utils.client_utils import insert_with_retry,generate_keys
from ..scripts import add_peer
import subprocess
import os
import sys
clients_manager_bp = Blueprint('clients', __name__,url_prefix='/clients')

@clients_manager_bp.route('clients/list_clients', methods=['GET'])
def list_clients():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM clients ORDER BY id ASC LIMIT ? OFFSET ?", (per_page, offset))
    clients = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM clients")
    total = cursor.fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    return render_template('clients/list_clients.html', clients=clients, page=page, total_pages=total_pages)

@clients_manager_bp.route('clients/add_clien_step1', methods=['GET','POST'])
def add_client_step1():
    form = AddClientForm()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM net_works")
    net_works = cursor.fetchall()
    form.net_work.choices = [(row['name']) for row in net_works]

    if form.validate_on_submit():
        client_name = form.name.data  
        net_work = form.net_work.data
        try:
            result = insert_with_retry(client_name,net_work)
            return redirect(url_for('clients.add_client_step2', client_id=result['id']))
        except Exception as e:
            flash(f"出错了: {str(e)}", "danger")
            return redirect(url_for('main.error'))

    return render_template('clients/add_step1.html', form=form)

@clients_manager_bp.route('clients/add_client_step2', methods=['get','POST'])
def add_client_step2():
    client_id = request.args.get('client_id')
    form = EmptyForm()
    if not client_id:
        flash("Missing client ID.", "danger")
        return redirect(url_for('main.error'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for('main.error'))

    if request.method == 'POST':
        try:
            keys = generate_keys()
            private_key = keys['private_key']
            public_key = keys['public_key']
            feature = client['feature']
            ip_address= client['ip_address']
            net_work = client['net_work']
            SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/generate_client_config.py')
            SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
            cmd = ['sudo','-n','/opt/wgmanager/venv/bin/python3', SCRIPT_PATH, feature, private_key, ip_address]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
              raise RuntimeError(f"Generate config failed: {result.stderr.strip()}")
            cursor.execute("""
                UPDATE clients SET private_key = ?, public_key = ? WHERE id = ?
            """, (private_key, public_key, client_id))
            db.commit()
            add_peer(public_key, client['ip_address'],net_work)
            flash(f"客户端 {feature} 添加成功！", "success")
            return redirect(url_for('main.succeed',form=form, client_id=client_id))

        except Exception as e:
            db.rollback()
            flash(f"Step 2 failed: {str(e)}", "danger")
            return redirect(url_for('main.error'))

    return render_template('clients/add_step2.html', form=form,client=client)

@clients_manager_bp.route('clients/delete_client_db_entry', methods=['get'])
def delete_client_db_entry():
    db = get_db()
    cursor = db.cursor()
    client_id = request.args.get('client_id')

    if not client_id:
        print(f"客户端 ID {client_id} 不存在。")
        return redirect(url_for('clients.list_clients'))
    try:
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        db.commit()
        print(f"客户端 ID {client_id} 已成功删除。")
    except Exception as e:
        db.rollback()
        print(f"删除客户端 ID {client_id} 时出错: {str(e)}")
    return redirect(url_for('clients.list_clients'))

@clients_manager_bp.route('clients/<client_id>/download')
def download_conf(client_id):
    client = get_client_from_db(client_id)
    server = get_interface_config(client['net_work'])

    conf = f"""[Interface]
PrivateKey = {client['private_key']}
Address = {client['ip_address']}
DNS = 8.8.8.8

[Peer]
PublicKey = {server['public_key']}
Endpoint = {server['ip_address']}:{server['listen_port']}
AllowedIPs = {client['allowed_ips']}
PersistentKeepalive = 25
"""

    return Response(
        conf,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={client['feature']}.conf'}
    )

def add_peer(public_key, ip_address, network):
    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/add_peer.py')
    SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
    flash(f"{sys.executable}{SCRIPT_PATH}", "info")

    cmd = ['sudo','-n','/opt/wgmanager/venv/bin/python3', SCRIPT_PATH,public_key, ip_address, network]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to add peer: {result.stderr}")
    return result.stdout

def get_client_from_db(client_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, name, feature, ip_address, private_key, public_key, allowed_ips, net_work
        FROM clients
        WHERE id = ?
    """, (client_id,))
    row = cursor.fetchone()
    if not row:
        raise Exception(f"Client with ID {client_id} not found")

    return {
        'id': row[0],
        'name': row[1],
        'feature': row[2],
        'ip_address': row[3],
        'private_key': row[4],
        'public_key': row[5],
        'allowed_ips': row[6],
        'net_work': row[7]
    }
  
def get_interface_config(net_work):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT name, ip_pool, public_key, listen_port
        FROM net_works
        WHERE name = ?
    """, (net_work,))
    row = cursor.fetchone()
    if not row:
        raise Exception(f"Interface {net_work} not found")

    return {
        'name': row[0],
        'ip_address': row[1],
        'public_key': row[2],
        'listen_port': row[3]
    }        

    
    