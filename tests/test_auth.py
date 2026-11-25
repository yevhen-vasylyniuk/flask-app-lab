import unittest

from flask_login import current_user

from app import create_app, db
from app.users.models import User


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def make_user(self, username="user1", email="user1@example.com", password="secret1"):
        user = User(username=username, email=email, password=User.hash_password(password))
        db.session.add(user)
        db.session.commit()
        return user

    def register(self, **overrides):
        data = {
            "username": "ivan_k",
            "email": "ivan@example.com",
            "password": "secret1",
            "confirm_password": "secret1",
        }
        data.update(overrides)
        return self.client.post("/users/register", data=data)

    def login(self, email="user1@example.com", password="secret1", **kwargs):
        return self.client.post("/users/login", data={"email": email, "password": password}, **kwargs)

    # --- Views Tests ---
    def test_register_page_loads(self):
        response = self.client.get("/users/register")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        for field in ("username", "email", "password", "confirm_password"):
            self.assertIn(f'name="{field}"', page)

    def test_login_page_loads(self):
        response = self.client.get("/users/login")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('name="email"', page)
        self.assertIn('name="remember"', page)

    # --- Реєстрація ---
    def test_register_saves_user_with_hashed_password(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/users/login")

        user = db.session.scalar(db.select(User).where(User.email == "ivan@example.com"))
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "ivan_k")
        self.assertNotEqual(user.password, "secret1")
        self.assertTrue(user.password.startswith("$2b$"))
        self.assertTrue(user.check_password("secret1"))

    def test_register_duplicate_username_and_email(self):
        self.make_user(username="ivan_k", email="ivan@example.com")
        response = self.register()
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ім&#39;ям уже існує", page)
        self.assertIn("уже зареєстрований", page)
        self.assertEqual(db.session.scalar(db.select(db.func.count(User.id))), 1)

    def test_register_validation_errors(self):
        response = self.register(username="1x", email="not-an-email", confirm_password="other")
        page = response.get_data(as_text=True)
        self.assertIn("від 4 до 14 символів", page)
        self.assertIn("Некоректна адреса email", page)
        self.assertIn("Паролі не збігаються", page)
        self.assertIsNone(db.session.scalar(db.select(User)))

    # --- Вхід і вихід ---
    def test_login_success(self):
        self.make_user()
        with self.client:
            response = self.login()
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, "/users/account")
            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(current_user.username, "user1")

        page = self.client.get("/users/account").get_data(as_text=True)
        self.assertIn("user1@example.com", page)
        self.assertIn("Вихід", page)        # меню для авторизованого
        self.assertNotIn("Реєстрація", page)

    def test_login_wrong_password(self):
        self.make_user()
        with self.client:
            response = self.login(password="wrong", follow_redirects=True)
            self.assertIn("Невірний email або пароль", response.get_data(as_text=True))
            self.assertFalse(current_user.is_authenticated)

    def test_logout(self):
        self.make_user()
        self.login()
        with self.client:
            response = self.client.post("/users/logout", follow_redirects=True)
            self.assertIn("Ви вийшли з системи", response.get_data(as_text=True))
            self.assertFalse(current_user.is_authenticated)
        self.assertEqual(self.client.get("/users/account").status_code, 302)

    # --- Захист сторінок (@login_required) ---
    def test_protected_pages_redirect_to_login(self):
        for url in ("/users/account", "/users/all", "/users/profile"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response.location.startswith("/users/login?next="), url)

    def test_login_redirects_back_to_next(self):
        self.make_user()
        response = self.client.post("/users/login?next=/users/all",
                                    data={"email": "user1@example.com", "password": "secret1"})
        self.assertEqual(response.location, "/users/all")

    def test_users_list_with_count(self):
        self.make_user()
        self.make_user(username="petro", email="petro@example.com")
        self.login()
        page = self.client.get("/users/all").get_data(as_text=True)
        self.assertIn("Усього: 2", page)
        self.assertIn("petro@example.com", page)

    def test_authenticated_user_redirected_from_register_and_login(self):
        self.make_user()
        self.login()
        self.assertEqual(self.client.get("/users/register").location, "/users/account")
        self.assertEqual(self.client.get("/users/login").location, "/users/account")


if __name__ == "__main__":
    unittest.main()
