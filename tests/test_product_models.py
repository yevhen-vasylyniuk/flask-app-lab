import unittest

from app import create_app, db
from app.products.models import Product, Category


class ProductModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def test_one_to_many_relationship(self):
        laptops = Category(name="Laptops")
        product = Product(name="Gaming Laptop", price=1500.0, category=laptops)
        db.session.add_all([laptops, product])
        db.session.commit()

        self.assertEqual(product.category.name, "Laptops")
        self.assertEqual(laptops.products, [product])

    def test_defaults(self):
        product = Product(name="iPhone 15", price=999.99)
        db.session.add(product)
        db.session.commit()

        self.assertTrue(product.active)
        self.assertIsNotNone(product.created_at)
        self.assertIsNone(product.category)

    def test_constraint_names_follow_convention(self):
        fk = next(iter(Product.__table__.foreign_keys)).constraint
        self.assertEqual(fk.name, "fk_products_category_id_categories")


if __name__ == "__main__":
    unittest.main()
