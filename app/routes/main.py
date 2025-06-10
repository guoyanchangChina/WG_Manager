from flask import Blueprint,render_template
from flask import redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@main_bp.route('/error')
def error():
    return render_template('error.html')

@main_bp.route('/succeed')
def succeed():
    return render_template('succeed.html')