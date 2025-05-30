from flask import Blueprint,render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/error')
def error():
    return render_template('error.html')

@main_bp.route('/succeed')
def succeed():
    return render_template('succeed.html')