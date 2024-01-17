from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import json, os

db = SQLAlchemy()
mail = Mail()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    j = open(os.getcwd() + '\\website\\static\\config.json')
    app.config["SECRET_KEY"] = json.load(j)["key"]
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from . import models
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return models.User.query.get(int(id))
    
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'lalarsek@gmail.com'
    app.config['MAIL_PASSWORD'] = "deor kemw dpom tatl"
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    global mail
    mail= Mail(app)

    return app