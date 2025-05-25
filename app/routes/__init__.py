from .auth import auth_bp
from .dashboard import dashboard_bp  
from .user_manager import user_manager_bp  
from .clients_manager import clients_manager_bp
from .main import main_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(user_manager_bp)
    app.register_blueprint(clients_manager_bp)