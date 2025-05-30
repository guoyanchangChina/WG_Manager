from flask import Blueprint, render_template, flash, redirect, url_for,request,session
from ..forms import EditUserForm,PasswordResetForm
from ..db import get_db
from ..extensions import bcrypt

user_manager_bp = Blueprint('users', __name__,url_prefix='/users')

@user_manager_bp.route('/list_users', methods=['GET'])
def list_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('users/list_users.html', users=users)

@user_manager_bp.route('/users/add', methods=['GET', 'POST'])
def add_user():
    form = EditUserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        department = form.department.data
        role = form.role.data
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, department, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, department, role)
        )
        db.commit()
        flash("用户添加成功", "success")
    return render_template('users/user_form.html', form=form, is_edit=False)
    

@user_manager_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return redirect(url_for('users.list_users'))

    form = EditUserForm(is_edit=True)
    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data
        department = form.department.data
        role = form.role.data
        action = request.form['action']
        if action == 'delete':
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            db.commit()
            return redirect(url_for('users.list_users'))
        elif action == 'save':
           if password:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute(
                "UPDATE users SET password_hash=?, department=?, role=?, WHERE id=?",
                (password_hash, department, role, user_id)
            )
           else:
            cursor.execute(
                "UPDATE users SET department=?, role=? WHERE id=?",
                (department, role, user_id)
            )

            db.commit()
            flash("用户信息更新成功", "success")
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            form.username.data = user['username']
            form.department.data = user['department']
            form.role.data = user['role']

            return render_template('users/user_form.html', form=form, is_edit=True)

    elif request.method == 'GET':
        form.username.data = user['username']
        form.department.data = user['department']
        form.role.data = user['role']

    return render_template('users/user_form.html', form=form, is_edit=True)

@user_manager_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    db = get_db()
    cursor = db.cursor()

    user_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        flash("用户不存在或已被删除。", "danger")
        return redirect(url_for('main.error'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        new_password = form.new_password.data
        hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor.execute(
            "UPDATE users SET password_hash = ?, is_password_reset = True WHERE id = ?",
            (hashed, user_id)
        )
        db.commit()
        return redirect(url_for('dashboard.dashboard'))  

    return render_template('users/reset_password.html', form=form)