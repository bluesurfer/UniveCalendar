import telebot

from flask import Flask

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.babel import Babel, lazy_gettext
from flask.ext.moment import Moment
from flask.ext.mail import Mail
from flask_wtf.csrf import CsrfProtect
from flask.ext.breadcrumbs import Breadcrumbs
from flask.json import JSONEncoder

from config import config, Config


class CustomJSONEncoder(JSONEncoder):
    """This class adds support for lazy translation texts to Flask's
    JSON encoder. This is necessary when flashing translated texts."""
    def default(self, obj):
        from speaklater import is_lazy_string

        if is_lazy_string(obj):
            try:
                return unicode(obj)  # python 2
            except NameError:
                return str(obj)  # python 3
        return super(CustomJSONEncoder, self).default(obj)


babel = Babel()
db = SQLAlchemy()
csrf = CsrfProtect()
breadcrumbs = Breadcrumbs()
moment = Moment()
mail = Mail()
bot = telebot.TeleBot(Config.BOT_TOKEN)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = lazy_gettext('Please login to access this page')


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.json_encoder = CustomJSONEncoder
    config[config_name].init_app(app)

    db.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    mail.init_app(app)
    breadcrumbs.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app