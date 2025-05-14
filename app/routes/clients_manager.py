from flask import Blueprint
from flask import render_template, flash, redirect, url_for, request
from ..db import get_db
from ..forms import AddClientForm
from ..utils.client_utils import insert_with_retry,generate_keys,generate_client_config,add_peer_to_server_config

clients_manager_bp = Blueprint('clients', __name__,url_prefix='/clients')


@clients_manager_bp.route('clients/list_clients', methods=['GET'])
def list_clients():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    return render_template('clients/list_clients.html', clients=clients)

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
            return redirect(url_for('clients.add_client_step1'))

    return render_template('clients/add_step1.html', form=form)

@clients_manager_bp.route('clients/add_client_step2', methods=['get','POST'])
def add_client_step2():
    client_id = request.args.get('client_id')

    if not client_id:
        flash("Missing client ID.", "danger")
        return redirect(url_for('clients.list_clients'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for('clients.list_clients'))

    if request.method == 'POST':
        try:
            keys = generate_keys()
            private_key = keys['private_key']
            public_key = keys['public_key']

            config_path = generate_client_config(client, private_key, public_key)

            cursor.execute("""
                UPDATE clients SET private_key = ?, public_key = ? WHERE id = ?
            """, (private_key, public_key, client_id))
            db.commit()

            add_peer_to_server_config(public_key, client['ip_address'])

            flash("Client fully configured.", "success")
            return redirect(url_for('clients.list_clients'))

        except Exception as e:
            db.rollback()
            flash(f"Step 2 failed: {str(e)}", "danger")
            return redirect(url_for('clients.add_client_step2', client_id=client_id))

    return render_template('clients/add_step2.html', client=client)

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