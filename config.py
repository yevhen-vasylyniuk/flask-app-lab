import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "dev-secret-key"

# Лог-файл для повідомлень з контактної форми
CONTACT_LOG = os.path.join(BASE_DIR, "logs", "contacts.log")

# TinyDB-сховище товарів
PRODUCTS_DB = os.path.join(BASE_DIR, "data", "products.json")

# Зображення товарів: каталог static/uploads блюпринта products
UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "products", "static", "uploads")
MAX_IMAGE_SIZE = 2 * 1024 * 1024        # 2 МБ на одне зображення
MAX_CONTENT_LENGTH = 5 * 1024 * 1024    # 5 МБ на весь запит
