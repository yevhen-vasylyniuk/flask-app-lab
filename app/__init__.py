import logging
import os

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from .config import config_map


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()


def configure_contact_logger(app):
    """Логер, який дописує повідомлення з контактної форми у файл."""
    logger = logging.getLogger("contact_form")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        os.makedirs(os.path.dirname(app.config["CONTACT_LOG"]), exist_ok=True)
        handler = logging.FileHandler(app.config["CONTACT_LOG"], encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)


def create_app(config_name=None):
    """Application factory: створює застосунок для вказаного середовища."""
    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    configure_contact_logger(app)

    from .views import main_bp
    app.register_blueprint(main_bp)

    from .users import user_bp
    app.register_blueprint(user_bp)

    from .products import products_bp
    app.register_blueprint(products_bp)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html", title="Сторінку не знайдено"), 404

    return app
