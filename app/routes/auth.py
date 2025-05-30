# app/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, login_required
from ..forms import LoginForm
from ..user_loader import get_user_by_username, User
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['get','POST'])
def login():
    from app import bcrypt
    form = LoginForm()
    if form.validate_on_submit():
        user_data = get_user_by_username(form.username.data)
        print(f"User row: {user_data}")
        if user_data and bcrypt.check_password_hash(user_data['password_hash'], form.password.data):
            session['username'] = user_data['username']
            session['role'] = user_data['role'] 
            session['user_id'] = user_data['id']
            user = User(user_data)
            login_user(user)
            if not user.is_password_reset:
                flash('检测到您使用的是初始密码，请先重置密码！', 'warning')
                return redirect(url_for('users.reset_password', user_id=user.id))
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('错误的用户名或密码', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout',methods=['get'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



