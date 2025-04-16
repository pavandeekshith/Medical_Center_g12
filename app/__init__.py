from flask import Flask, render_template
from app.config import Config
import logging
import os
from flask_bcrypt import Bcrypt
from app.utils.database import init_db

bcrypt = Bcrypt()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='medical_center.log'
)
logger = logging.getLogger('medical_center')

def create_app(config_class=Config):
    """
    Create and configure the Flask application
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize bcrypt
    bcrypt.init_app(app)
    
    # Initialize database
    init_db()
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Register blueprints
    from app.views.main import main
    from app.views.doctor import doctor
    from app.views.staff import staff
    from app.views.student import student
    from app.auth.routes import auth
    from app.views.api import api
    
    app.register_blueprint(main)
    app.register_blueprint(doctor, url_prefix='/doctor')
    app.register_blueprint(staff, url_prefix='/staff')
    app.register_blueprint(student, url_prefix='/student')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(api, url_prefix='/api')
    
    # Add template filters
    @app.template_filter('b64encode')
    def b64encode_filter(data):
        import base64
        if data:
            return base64.b64encode(data).decode('utf-8')
        return ''
    
    # Add context processors
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    # Clean up database connections when app context ends
    @app.teardown_appcontext
    def close_db_connection(exception):
        from app.utils.database import get_db_connection
        db = getattr(app, '_database', None)
        if db is not None:
            db.close()
    
    # Log application startup
    logger.info('Application started')
    
    return app
