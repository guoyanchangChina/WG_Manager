from flask import Blueprint,render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/error')
def error():
    return render_template('error.html')