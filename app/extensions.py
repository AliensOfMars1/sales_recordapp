from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

def init_login_manager(app):
    """Initialize login manager with user loader that can load both Admin and Barber"""
    from app.models import Admin, Barber
    
    @login_manager.user_loader
    def load_user(user_id):
        # First try Admin
        admin = Admin.query.get(int(user_id))
        if admin:
            return admin
        # Then try Barber
        return Barber.query.get(int(user_id))
    
    login_manager.init_app(app)