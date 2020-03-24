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

def create_app(config_class=Config):
    # ...
    if not app.debug and not app.testing:
        # ...

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/microblog.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app

from app import routes, models, errors