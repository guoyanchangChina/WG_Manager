from flask import Blueprint,render_template
from ..db import get_db
from ..forms import AddInterfaceForm
from ..utils import system_utils
from flask import flash, redirect, url_for
import os,subprocess    
from flask_login import current_user

system_bp = Blueprint('system', __name__,)

@system_bp.route('/settings')
def show_settings():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM net_works ORDER BY created_at DESC")
    net_works = cursor.fetchall()
    return render_template('system/settings.html', net_works=net_works)

@system_bp.route('/add_net_work', methods=['POST','GET'])
def add_net_work():
    form = AddInterfaceForm()
    if form.validate_on_submit():
     try:
        db = get_db()
        cursor = db.cursor()
        listen_port = system_utils.get_next_available_port() 
        interface_name = form.interface_name.data
        prefix = int (form.address.data)
        ip_pool = system_utils.get_next_available_subnet(int(prefix))
        gate_way = f"{ip_pool.split('.')[0]}.{ip_pool.split('.')[1]}.{ip_pool.split('.')[2]}.1/32"  
        server_ip = form.server_ip.data
        created_by = current_user.username
        SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/add_net_work.py')
        SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
        cmd = ['sudo','-n','/opt/wgmanager/venv/bin/python3', SCRIPT_PATH, interface_name, gate_way, str(listen_port)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            flash(f"系统错误,请联系管理员:Error creating interface: {result.stderr}", "danger")
            return redirect(url_for('main.error'))
        lines = result.stdout.strip().splitlines()
        if len(lines) >= 2:
            private_key, public_key = lines[-2], lines[-1]
        else:
            flash("系统错误,请联系管理员:Failed to parse key pair from script output.", "danger")
            return redirect(url_for('main.error'))
        cursor.execute("""
            INSERT INTO net_works (name, ip_pool, gate_way, server_ip, private_key, public_key, listen_port, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interface_name,
            ip_pool,
            gate_way,
            server_ip,
            private_key,
            public_key,
            listen_port,
            created_by 
            ))
        db.commit()
        return redirect(url_for('system.show_settings'))
     except Exception as e:
        flash(f"添加虚拟网络出错: {str(e)}", "danger")
        return redirect(url_for('main.error'))

    return render_template('system/add_net_work.html', form=form)