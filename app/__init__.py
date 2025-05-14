from flask import Flask,redirect,url_for,request
from flask_login import LoginManager,current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from .routes import register_routes
from .db import close_db
from dotenv import load_dotenv
import os
from .extensions import bcrypt

login_manager = LoginManager()
csrf = CSRFProtect()

load_dotenv()

from .user_loader import get_user_by_id
login_manager.user_loader(get_user_by_id)

def create_app():
    app = Flask(__name__,template_folder='../templates',static_folder='../static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','testkkk')
    app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('WTF_CSRF_SECRET_KEY','testkkk')
    app.config['DATABASE'] = 'instance/xlyvpn.db'

    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    app.teardown_appcontext(close_db)
    @app.before_request
    def check_login():
        allowed_endpoints = ['auth.login', 'static'] 
        if (
            request.endpoint not in allowed_endpoints  
            and not current_user.is_authenticated  
        ):
            return redirect(url_for('auth.login'))  

    register_routes(app)

    return app