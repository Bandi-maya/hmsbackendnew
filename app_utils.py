from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


db = SQLAlchemy()
ma = Marshmallow()

app = Flask(__name__)
cors = CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hms:hms_main_123@91.108.104.49:5432/hms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'koyiladavignesh@gmail.com'
app.config['MAIL_PASSWORD'] = 'hspbpbidfdxigfvv'

mail = Mail(app)

db.init_app(app)
ma.init_app(app)
api = Api(app)

app.config['JWT_SECRET_KEY'] = 'qxYAaIjjura3OEa2GNbbUnifmvuauEKorWCwNOw6xlo'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)


jwt = JWTManager(app)

def send_email(subject, recipients, body, sender='your_email@gmail.com'):
    msg = Message(subject=subject,
                  sender=sender,
                  recipients=recipients,
                  body=body)
    mail.send(msg)
