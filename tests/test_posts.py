import unittest
from datetime import datetime

from app import create_app, db
from app.posts.models import Post
from app.users.models import User


class PostsTestCase(unittest.TestCase):
    def setUp(self):
        """Тестовий застосунок з in-memory SQLite і чистими таблицями."""
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

    def make_post(self, **fields):
        data = {"title": "Test post", "content": "Test content", "category": "tech"}
        data.update(fields)
        post = Post(**data)
        db.session.add(post)
        db.session.commit()
        return post

    def form_data(self, **overrides):
        data = {
            "title": "Новий пост",
            "content": "Текст нового поста",
            "enabled": "y",
            "publish_date": "2026-11-20T10:30",
            "category": "news",
        }
        data.update(overrides)
        return data

    # US01 — створення поста
    def test_create_post(self):
        response = self.client.post("/post/create", data=self.form_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/post")

        post = db.session.scalar(db.select(Post))
        self.assertEqual(post.title, "Новий пост")
        self.assertEqual(post.category, "news")
        self.assertEqual(post.posted, datetime(2026, 11, 20, 10, 30))
        self.assertTrue(post.is_active)
        self.assertIsNone(post.user)

        page = self.client.get(response.location).get_data(as_text=True)
        self.assertIn("Пост успішно додано", page)

    def make_user(self, username="user1"):
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user

    def test_create_post_author_from_session(self):
        self.make_user("user1")
        with self.client.session_transaction() as session:
            session["username"] = "user1"
        self.client.post("/post/create", data=self.form_data())
        self.assertEqual(db.session.scalar(db.select(Post)).user.username, "user1")

    def test_create_post_invalid(self):
        response = self.client.post("/post/create", data=self.form_data(title="", content=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Вкажіть заголовок", response.get_data(as_text=True))
        self.assertIsNone(db.session.scalar(db.select(Post)))

    def test_create_form_page(self):
        response = self.client.get("/post/create")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="publish_date"', response.data)
        self.assertNotIn(b'name="author"', response.data)

    # US02 — список постів
    def test_list_posts(self):
        self.make_post(title="Old post", posted=datetime(2026, 1, 1))
        self.make_post(title="New post", posted=datetime(2026, 6, 1))
        self.make_post(title="Hidden post", is_active=False)

        response = self.client.get("/post")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertLess(page.index("New post"), page.index("Old post"))  # новіші вище
        self.assertNotIn("Hidden post", page)

    # US03 — перегляд поста
    def test_view_post_detail(self):
        post = self.make_post(title="Detail post", content="Full content", user=self.make_user("user1"))
        response = self.client.get(f"/post/{post.id}")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for text in ("Detail post", "Full content", "user1"):
            self.assertIn(text, page)

    # US04 — редагування поста
    def test_update_form_prefilled(self):
        post = self.make_post(title="Old title", posted=datetime(2026, 3, 5, 8, 15))
        response = self.client.get(f"/post/{post.id}/update")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="Old title"', response.data)
        self.assertIn(b'value="2026-03-05T08:15"', response.data)

    def test_update_post(self):
        author = self.make_user("user1")
        post = self.make_post(title="Old title", user=author)
        response = self.client.post(
            f"/post/{post.id}/update",
            data=self.form_data(title="New title", category="other", enabled=""),
        )
        self.assertEqual(response.status_code, 302)

        updated = db.session.get(Post, post.id)
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.category, "other")
        self.assertFalse(updated.is_active)
        self.assertEqual(updated.user, author)  # автор не змінюється

    # US05 — видалення поста
    def test_delete_confirm_page(self):
        post = self.make_post(title="To delete")
        response = self.client.get(f"/post/{post.id}/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn("To delete", response.get_data(as_text=True))
        self.assertIsNotNone(db.session.get(Post, post.id))

    def test_delete_post(self):
        post = self.make_post()
        response = self.client.post(f"/post/{post.id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Пост видалено", response.get_data(as_text=True))
        self.assertIsNone(db.session.get(Post, post.id))

    # US06 — 404
    def test_404_not_found(self):
        self.assertEqual(self.client.get("/post/999").status_code, 404)
        self.assertEqual(self.client.get("/post/999/update").status_code, 404)
        response = self.client.get("/nonexistent-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Сторінку не знайдено", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
