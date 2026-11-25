import os

from dotenv import load_dotenv

load_dotenv()  # завантажує змінні з .env

# Корінь проєкту (на рівень вище папки app)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """Базова конфігурація для всіх середовищ."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Журнал SQL-запитів вмикається змінною середовища: SQLALCHEMY_ECHO=1 flask shell
    SQLALCHEMY_ECHO = os.environ.get("SQLALCHEMY_ECHO") == "1"

    # Лог-файл для повідомлень з контактної форми
    CONTACT_LOG = os.path.join(BASE_DIR, "logs", "contacts.log")

    # TinyDB-сховище товарів
    PRODUCTS_DB = os.path.join(BASE_DIR, "data", "products.json")

    # Зображення товарів: каталог static/uploads блюпринта products
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "products", "static", "uploads")
    MAX_IMAGE_SIZE = 2 * 1024 * 1024        # 2 МБ на одне зображення
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024    # 5 МБ на весь запит


class DevelopmentConfig(Config):
    """Режим розробки: налагодження і локальна SQLite у папці instance."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.sqlite")


class TestingConfig(Config):
    """Тести: окрема in-memory SQLite, без CSRF."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Продакшн: без налагодження, база з DATABASE_URL."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///prod.sqlite")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
