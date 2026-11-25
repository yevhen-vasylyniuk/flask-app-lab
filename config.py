import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "dev-secret-key"

# Лог-файл для повідомлень з контактної форми
CONTACT_LOG = os.path.join(BASE_DIR, "logs", "contacts.log")
