from flask import Blueprint,render_template, redirect, url_for

main_bp = Blueprint('main', __name__)
@main_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@main_bp.route('/error')
def error():
    return render_template('error.html')