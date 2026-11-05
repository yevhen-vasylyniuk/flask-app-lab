import unittest
from app import app


class ProductsTestCase(unittest.TestCase):
    def setUp(self):
        """Налаштування клієнта тестування перед кожним тестом."""
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_products_list(self):
        """Тест маршруту /products/ — відображаються всі товари."""
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn(b"Phone", response.data)
        self.assertIn(b"PC", response.data)

    def test_product_detail(self):
        """Тест маршруту /products/<id> для існуючого товару."""
        response = self.client.get("/products/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn(b"1200", response.data)

    def test_product_not_found(self):
        """Тест маршруту /products/<id> для неіснуючого товару."""
        response = self.client.get("/products/99")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
