import logging
import os
from flask import Flask, jsonify
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
compress = Compress()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    
    # Validate config name
    if config_name not in config:
        logger.warning(f"Invalid config name '{config_name}', using 'development'")
        config_name = 'development'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Proxy fix for production deployments
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    compress.init_app(app)
    jwt.init_app(app)
    
    # Initialize rate limiter with Redis if available
    if app.config.get('REDIS_URL'):
        limiter.storage_uri = app.config['REDIS_URL']
    limiter.init_app(app)
    
    # Configure CORS properly for mobile and web
    CORS(app, 
         origins=app.config['CORS_ORIGINS'] + ['http://localhost:*', 'http://127.0.0.1:*'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         expose_headers=['Content-Type', 'Authorization'],
         max_age=3600)
    
    logger.info(f"[OK] CORS configured for origins: {app.config['CORS_ORIGINS']}")
    
    # Initialize services
    with app.app_context():
        # Import models
        from app import models
        
        # Initialize FAISS service
        try:
            from app.services.faiss_service import faiss_service
            faiss_service.initialize(app.config)
            logger.info("[OK] FAISS service initialized")
        except Exception as e:
            logger.error(f"[ERROR] FAISS initialization failed: {e}")
        
        # Initialize cache service
        try:
            from app.services.cache_service import cache_service
            cache_service.initialize(app.config.get('REDIS_URL'))
            logger.info("[OK] Cache service initialized")
        except Exception as e:
            logger.warning(f"[WARNING] Cache service unavailable: {e}")
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check and utilities
    register_health_check(app)
    
    # Register CLI commands
    register_commands(app)
    
    logger.info(f"[OK] Application created: {config_name} mode")
    
    return app


def register_blueprints(app):
    """Register all API blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.enrollment import enrollment_bp
    from app.routes.attendance import attendance_bp
    from app.routes.admin import admin_bp
    from app.routes.super_admin import super_admin_bp
    from app.routes.user import user_bp
    from app.routes.face import face_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(enrollment_bp, url_prefix='/api/enrollment')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(super_admin_bp, url_prefix='/api/super-admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(face_bp, url_prefix='/api/face')
    
    logger.info("[OK] API Blueprints registered")


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden", "message": "Insufficient permissions"}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "Resource not found"}), 404
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({"error": "Rate limit exceeded", "message": str(error)}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception(f"Unhandled exception: {error}")
        return jsonify({"error": "Internal server error", "details": str(error) if app.debug else None}), 500


def register_health_check(app):
    
    @app.route('/')
    @app.route('/api')
    def index():
        """API information"""
        return jsonify({
            "name": "Smart Attendance System API",
            "version": "2.0.0",
            "status": "running",
            "features": [
                "Mobile-responsive",
                "Advanced face recognition",
                "Super admin support",
                "Real-time attendance tracking",
                "Multi-device support"
            ],
            "endpoints": {
                "auth": "/api/auth",
                "enrollment": "/api/enrollment",
                "attendance": "/api/attendance",
                "admin": "/api/admin",
                "super-admin": "/api/super-admin",
                "user": "/api/user",
                "face": "/api/face",
                "health": "/health"
            }
        })
    
    @app.route('/health')
    def health_check():
        """Comprehensive health check"""
        from app.services.faiss_service import faiss_service
        from app.services.cache_service import cache_service
        from sqlalchemy import text
        
        health = {
            "status": "healthy",
            "version": "2.0.0",
            "checks": {}
        }
        
        # Check database
        try:
            with db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                conn.commit()
            health["checks"]["database"] = "healthy"
        except Exception as e:
            health["checks"]["database"] = f"unhealthy: {str(e)}"
            health["status"] = "unhealthy"
        
        # Check cache
        try:
            if cache_service.is_available():
                cache_service.ping()
                health["checks"]["cache"] = "healthy"
            else:
                health["checks"]["cache"] = "not_configured"
        except Exception as e:
            health["checks"]["cache"] = f"unhealthy: {str(e)}"
        
        # Check FAISS
        try:
            total = faiss_service.get_total_persons()
            health["checks"]["faiss"] = f"healthy ({total} persons indexed)"
        except Exception as e:
            health["checks"]["faiss"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"
        
        status_code = 200 if health["status"] in ["healthy", "degraded"] else 503
        return jsonify(health), status_code


def register_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize database and create tables"""
        db.create_all()
        print("[OK] Database initialized")
    
    @app.cli.command()
    def create_super_admin():
        """Create super admin user"""
        from app.models import Admin
        from werkzeug.security import generate_password_hash
        
        email = input("Email: ")
        password = input("Password: ")
        name = input("Name: ")
        
        admin = Admin(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role='super_admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"[OK] Super Admin created: {email}")
    
    @app.cli.command()
    def rebuild_faiss():
        """Rebuild FAISS index from database"""
        from app.services.faiss_service import faiss_service
        faiss_service.rebuild_from_database()
        print("[OK] FAISS index rebuilt")
