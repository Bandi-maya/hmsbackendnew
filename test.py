from configure_routes import configure_routes
from extentions import db, ma, mail, jwt, api, cors
from app_utils import app

db.init_app(app)
ma.init_app(app)
api.init_app(app)
mail.init_app(app)
jwt.init_app(app)
cors.init_app(app)
