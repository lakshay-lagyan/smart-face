"""Application entry point"""
import os
from app import create_app, db
from app.models import Admin, User, Person, Attendance, EnrollmentRequest, SystemLog, Settings

# Get config from environment
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

# Shell context for flask shell command
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Admin': Admin,
        'User': User,
        'Person': Person,
        'Attendance': Attendance,
        'EnrollmentRequest': EnrollmentRequest,
        'SystemLog': SystemLog,
        'Settings': Settings
    }

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = config_name == 'development'
    
    app.run(host=host, port=port, debug=debug)
