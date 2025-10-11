# This file breaks circular imports by creating extension objects here.
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
ma = Marshmallow()
mail = Mail()
api = Api()
jwt = JWTManager()
cors = CORS()
