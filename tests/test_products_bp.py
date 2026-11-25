import io
import json
import os
import shutil
import tempfile
import unittest

from app import create_app


class ProductsCrudTestCase(unittest.TestCase):
    def setUp(self):
        """Окрема тимчасова TinyDB і папка для зображень на кожен тест."""
        self.tmp_dir = tempfile.mkdtemp()
        self.app = create_app("testing")
        self.app.config.update(
            PRODUCTS_DB=os.path.join(self.tmp_dir, "products.json"),
            UPLOAD_FOLDER=os.path.join(self.tmp_dir, "uploads"),
        )
        self.client = self.app.test_client()
        self.client.get("/product")  # ініціалізує сховище початковими товарами

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def product_data(self, **overrides):
        data = {
            "name": "Mouse",
            "content": "Бездротова миша",
            "price": "19.99",
            "category": "accessories",
            "quantity": "15",
        }
        data.update(overrides)
        return data

    def stored_products(self):
        with open(self.app.config["PRODUCTS_DB"], encoding="utf-8") as f:
            return json.load(f)["products"]

    def uploaded_files(self):
        folder = self.app.config["UPLOAD_FOLDER"]
        return os.listdir(folder) if os.path.exists(folder) else []

    # --- Read ---
    def test_products_list(self):
        """GET /product — список початкових товарів."""
        response = self.client.get("/product")
        self.assertEqual(response.status_code, 200)
        for name in (b"Laptop", b"Phone", b"PC"):
            self.assertIn(name, response.data)

    def test_product_detail(self):
        """GET /product/<id> — повна інформація про товар."""
        response = self.client.get("/product/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn(b"1200.00", response.data)

    def test_product_not_found(self):
        """GET /product/<id> для неіснуючого товару повертає 404."""
        response = self.client.get("/product/99")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Товар не знайдено", response.get_data(as_text=True))

    # --- Create ---
    def test_add_product(self):
        """POST /product/add — товар зберігається з id і created_at, PRG-редірект."""
        response = self.client.post("/product/add", data=self.product_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/product/4")

        product = self.stored_products()["4"]
        self.assertEqual(product["name"], "Mouse")
        self.assertEqual(product["price"], 19.99)
        self.assertEqual(product["quantity"], 15)
        self.assertIsNone(product["image"])
        self.assertTrue(product["created_at"])

        page = self.client.get(response.location).get_data(as_text=True)
        self.assertIn("успішно додано", page)

    def test_add_product_with_image(self):
        """Зображення зберігається з UUID-ім'ям, у БД — відносний шлях."""
        data = self.product_data(image=(io.BytesIO(b"fake png"), "photo.png"))
        self.client.post("/product/add", data=data, content_type="multipart/form-data")

        image = self.stored_products()["4"]["image"]
        self.assertTrue(image.startswith("uploads/") and image.endswith(".png"))
        self.assertNotIn("photo", image)
        self.assertEqual(self.uploaded_files(), [os.path.basename(image)])

    def test_add_product_invalid(self):
        """Невалідні дані не зберігаються, показуються помилки."""
        data = self.product_data(name="ab", price="-5", quantity="-1", category="")
        response = self.client.post("/product/add", data=data)
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("щонайменше 3 символи", page)
        self.assertIn("Ціна має бути додатною", page)
        self.assertIn("Оберіть категорію", page)
        self.assertNotIn("4", self.stored_products())

    def test_add_product_wrong_image_type(self):
        """Файл з недозволеним розширенням відхиляється."""
        data = self.product_data(image=(io.BytesIO(b"gif"), "anim.gif"))
        response = self.client.post("/product/add", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PNG, JPG або JPEG", response.get_data(as_text=True))
        self.assertEqual(self.uploaded_files(), [])

    # --- Update ---
    def test_edit_product_keeps_id_created_at_and_image(self):
        """Редагування без нового файлу зберігає id, created_at і зображення."""
        data = self.product_data(image=(io.BytesIO(b"png"), "photo.png"))
        self.client.post("/product/add", data=data, content_type="multipart/form-data")
        before = self.stored_products()["4"]

        response = self.client.post("/product/4/edit", data=self.product_data(name="Mouse Pro", price="25.50"))
        self.assertEqual(response.status_code, 302)

        after = self.stored_products()["4"]
        self.assertEqual(after["name"], "Mouse Pro")
        self.assertEqual(after["price"], 25.5)
        self.assertEqual(after["created_at"], before["created_at"])
        self.assertEqual(after["image"], before["image"])

    def test_edit_product_replaces_image(self):
        """Нове зображення замінює старе, старий файл видаляється."""
        self.client.post("/product/add", content_type="multipart/form-data",
                         data=self.product_data(image=(io.BytesIO(b"old"), "old.png")))
        old_image = self.stored_products()["4"]["image"]

        self.client.post("/product/4/edit", content_type="multipart/form-data",
                         data=self.product_data(image=(io.BytesIO(b"new"), "new.jpg")))
        new_image = self.stored_products()["4"]["image"]

        self.assertNotEqual(new_image, old_image)
        self.assertEqual(self.uploaded_files(), [os.path.basename(new_image)])

    def test_edit_form_prefilled(self):
        """GET /product/<id>/edit показує поточні дані товару."""
        response = self.client.get("/product/2/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="Phone"', response.data)
        self.assertIn(b"800.00", response.data)

    # --- Delete ---
    def test_delete_product(self):
        """POST /product/<id>/delete видаляє товар і його зображення."""
        self.client.post("/product/add", content_type="multipart/form-data",
                         data=self.product_data(image=(io.BytesIO(b"png"), "photo.png")))

        response = self.client.post("/product/4/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("видалено", response.get_data(as_text=True))
        self.assertNotIn("4", self.stored_products())
        self.assertEqual(self.uploaded_files(), [])
        self.assertEqual(self.client.get("/product/4").status_code, 404)

    def test_delete_requires_post(self):
        """GET на маршрут видалення не дозволений."""
        response = self.client.get("/product/1/delete")
        self.assertEqual(response.status_code, 405)
        self.assertIn("1", self.stored_products())

    def test_ids_not_reused_after_delete(self):
        """Після видалення новий товар отримує новий id."""
        self.client.post("/product/add", data=self.product_data())
        self.client.post("/product/4/delete")
        response = self.client.post("/product/add", data=self.product_data())
        self.assertEqual(response.location, "/product/5")


if __name__ == "__main__":
    unittest.main()
