from flask import Blueprint
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

    if form.validate_on_submit():
        client_name = form.name.data  

        try:
            result = insert_with_retry(client_name)
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
            print("Before generate client config")
            config_path = generate_client_config(feature, private_key, public_key)
            print(f"config_path: {config_path}")
            cursor.execute("""
                UPDATE clients SET private_key = ?, public_key = ? WHERE id = ?
            """, (private_key, public_key, client_id))
            db.commit()
            flash(f"Before add peer", "danger")
            print("Before add peer")
            add_peer(public_key, client['ip_address'])

            flash("Client fully configured.", "success")
            return redirect(url_for('clieents.add_client_step3',form=form, client_id=client_id))

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

def add_peer(public_key, ip_address):
    flash(f"{sys.executable}", "info")
    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../app/scripts/add_peer.py')
    SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
    cmd = ['sudo','-n','/opt/wgmanager/venv/bin/python', SCRIPT_PATH,public_key, ip_address]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to add peer: {result.stderr}")
    return result.stdout

def generate_client_config(feature, private_key, ip_address):
    flash(f"{sys.executable}", "info")
    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../app/scripts/generate_client_config.py')
    SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
    cmd = ['sudo','-n','/opt/wgmanager/venv/bin/python', SCRIPT_PATH, feature, private_key, ip_address]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Generate config failed: {result.stderr.strip()}")
    return result.stdout.strip()