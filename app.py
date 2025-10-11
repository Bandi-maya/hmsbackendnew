import os
from datetime import timedelta
from flask import Flask, send_from_directory
from dotenv import load_dotenv

from configure_routes import configure_routes
from extentions import api

load_dotenv()


def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('MASTER_DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

    print(os.environ.get('MASTER_DATABASE_URL'))
    configure_routes(api)

    # --- Static File Route ---
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        # Use os.path.join for constructing paths
        return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)

    return app
