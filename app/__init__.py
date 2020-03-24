from flask import Flask, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bootstap = Bootstrap(app)
migrate = Migrate(app, db)
moment = Moment(app)
babel = Babel(app)
login = LoginManager(app)
login.login_message = _l("Please login to access this page.")
login.login_view = "login"
mail = Mail(app)

@babel.localeselector
def get_locale():
    try:
        language = current_user.language  # Anonymous users don't have it
        if not language:
            raise AttributeError
    except AttributeError:
        language = session.get("language") or \
        request.accept_languages.best_match(app.config.get("LANGUAGES"))
    return language

from app import routes, models, errors