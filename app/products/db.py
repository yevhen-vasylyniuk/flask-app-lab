import os
from datetime import datetime

from flask import current_app
from tinydb import TinyDB
from tinydb.table import Document

# Початкові товари, якими заповнюється нове сховище
SEED_PRODUCTS = [
    {
        "name": "Laptop",
        "content": "Потужний ноутбук з процесором Intel Core i7, 16 ГБ оперативної пам’яті та SSD на 512 ГБ.",
        "price": 1200.00,
        "category": "laptops",
        "quantity": 10,
    },
    {
        "name": "Phone",
        "content": "Смартфон із 6.5-дюймовим OLED-дисплеєм, подвійною камерою та акумулятором на 5000 мА·год.",
        "price": 800.00,
        "category": "phones",
        "quantity": 25,
    },
    {
        "name": "PC",
        "content": "Настільний комп’ютер для ігор або роботи з графікою: RTX 4070, 32 ГБ RAM, 1 ТБ SSD.",
        "price": 1800.00,
        "category": "pc",
        "quantity": 5,
    },
]


def _open_db():
    path = current_app.config["PRODUCTS_DB"]
    is_new = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    db = TinyDB(path, ensure_ascii=False, indent=2, encoding="utf-8")
    if is_new:
        now = _now()
        db.table("products").insert_multiple(
            dict(p, image=None, created_at=now) for p in SEED_PRODUCTS
        )
    return db


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_dict(doc):
    return dict(doc, id=doc.doc_id)


def get_all():
    with _open_db() as db:
        return [_to_dict(doc) for doc in db.table("products").all()]


def get_by_id(product_id):
    with _open_db() as db:
        doc = db.table("products").get(doc_id=product_id)
        return _to_dict(doc) if doc else None


def create(data):
    with _open_db() as db:
        products = db.table("products")
        meta = db.table("meta")

        # Лічильник у таблиці meta гарантує, що id видалених товарів не використаються повторно
        counter = meta.get(doc_id=1)
        last_id = max([counter["last_id"] if counter else 0] + [doc.doc_id for doc in products.all()])
        new_id = last_id + 1

        products.insert(Document(dict(data, created_at=_now()), doc_id=new_id))
        meta.upsert(Document({"last_id": new_id}, doc_id=1))
        return new_id


def update(product_id, data):
    # id і created_at не змінюються: оновлюються лише передані поля
    data = {k: v for k, v in data.items() if k not in ("id", "created_at")}
    with _open_db() as db:
        return bool(db.table("products").update(data, doc_ids=[product_id]))


def delete(product_id):
    with _open_db() as db:
        return bool(db.table("products").remove(doc_ids=[product_id]))
