"""Insert data into products table

Revision ID: e4e501681a10
Revises: 8523e870278a
Create Date: 2026-11-26 00:07:15.408611

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = 'e4e501681a10'
down_revision = '8523e870278a'
branch_labels = None
depends_on = None

CATEGORIES = ['Electronics', 'Books', 'Clothing']

PRODUCTS = [
    {'name': 'Laptop', 'price': 1200.0, 'active': True, 'category': 'Electronics'},
    {'name': 'Smartphone LG', 'price': 800.0, 'active': True, 'category': 'Electronics'},
    {'name': 'Novel', 'price': 20.0, 'active': True, 'category': 'Books'},
    {'name': 'T-Shirt', 'price': 25.0, 'active': False, 'category': 'Clothing'},
]


def upgrade():
    # --- Описи таблиць для bulk_insert ---
    categories_table = table('categories', column('id', sa.Integer), column('name', sa.String))

    # --- Вставка категорій ---
    op.bulk_insert(categories_table, [{'name': name} for name in CATEGORIES])

    # --- Вставка продуктів ---
    # category_id беремо за назвою категорії, а не жорстко заданим числом,
    # бо в таблиці вже можуть бути інші категорії (наприклад, Laptops з id=1)
    for product in PRODUCTS:
        op.execute(
            sa.text(
                "INSERT INTO products (name, price, active, category_id) "
                "SELECT :name, :price, :active, id FROM categories WHERE name = :category"
            ).bindparams(**product)
        )


def downgrade():
    # Видаляємо тільки вставлені продукти та категорії
    product_names = ", ".join(f"'{p['name']}'" for p in PRODUCTS)
    category_names = ", ".join(f"'{name}'" for name in CATEGORIES)
    op.execute(f"DELETE FROM products WHERE name IN ({product_names})")
    op.execute(f"DELETE FROM categories WHERE name IN ({category_names})")
