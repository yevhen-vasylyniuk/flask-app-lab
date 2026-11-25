import unittest
from datetime import datetime

from app import create_app, db
from app.posts.models import Post, Tag
from app.users.models import User


class PostsTestCase(unittest.TestCase):
    def setUp(self):
        """Тестовий застосунок з in-memory SQLite і чистими таблицями."""
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.author = self.make_user("author")
        self.other = self.make_user("petro")

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
            "author_id": str(self.author.id),
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
        self.assertEqual(post.user, self.author)

        page = self.client.get(response.location).get_data(as_text=True)
        self.assertIn("Пост успішно додано", page)

    def make_user(self, username="user1"):
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user

    def test_create_form_preselects_session_user(self):
        with self.client.session_transaction() as session:
            session["username"] = "petro"
        response = self.client.get("/post/create")
        self.assertIn(f'<option selected value="{self.other.id}">petro</option>', response.get_data(as_text=True))

    def test_create_post_with_selected_author(self):
        self.client.post("/post/create", data=self.form_data(author_id=str(self.other.id)))
        post = db.session.scalar(db.select(Post))
        self.assertEqual(post.user.username, "petro")
        self.assertIn(post, self.other.posts)

    def test_create_post_invalid(self):
        response = self.client.post("/post/create", data=self.form_data(title="", content=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Вкажіть заголовок", response.get_data(as_text=True))
        self.assertIsNone(db.session.scalar(db.select(Post)))

    def test_create_form_page(self):
        response = self.client.get("/post/create")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('name="publish_date"', page)
        self.assertIn('name="author_id"', page)  # список авторів з БД
        self.assertIn(">author</option>", page)
        self.assertIn(">petro</option>", page)

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
        post = self.make_post(title="Old title", posted=datetime(2026, 3, 5, 8, 15), user=self.other)
        response = self.client.get(f"/post/{post.id}/update")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="Old title"', response.data)
        self.assertIn(b'value="2026-03-05T08:15"', response.data)
        self.assertIn(f'<option selected value="{self.other.id}">petro</option>'.encode(), response.data)

    def test_update_post(self):
        post = self.make_post(title="Old title", user=self.author)
        response = self.client.post(
            f"/post/{post.id}/update",
            data=self.form_data(title="New title", category="other", enabled="",
                                author_id=str(self.other.id)),
        )
        self.assertEqual(response.status_code, 302)

        updated = db.session.get(Post, post.id)
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.category, "other")
        self.assertFalse(updated.is_active)
        self.assertEqual(updated.user, self.other)  # автора змінено через список

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

    # Теги (зв'язок «багато до багатьох»)
    def make_tags(self, *names):
        tags = [Tag(name=name) for name in names]
        db.session.add_all(tags)
        db.session.commit()
        return tags

    def test_create_post_with_tags(self):
        flask_tag, python_tag, _ = self.make_tags("Flask", "Python", "Study")
        self.client.post("/post/create", data=self.form_data(tags=[str(flask_tag.id), str(python_tag.id)]))
        post = db.session.scalar(db.select(Post))
        self.assertEqual({tag.name for tag in post.tags}, {"Flask", "Python"})
        self.assertIn(post, flask_tag.posts)

    def test_update_post_tags(self):
        flask_tag, python_tag = self.make_tags("Flask", "Python")
        post = self.make_post(user=self.author, tags=[flask_tag])

        response = self.client.get(f"/post/{post.id}/update")
        self.assertIn(f'<option selected value="{flask_tag.id}">Flask</option>', response.get_data(as_text=True))

        self.client.post(f"/post/{post.id}/update", data=self.form_data(tags=[str(python_tag.id)]))
        self.assertEqual([tag.name for tag in db.session.get(Post, post.id).tags], ["Python"])

    def test_detail_shows_tags(self):
        tags = self.make_tags("Flask", "Python")
        post = self.make_post(tags=tags)
        page = self.client.get(f"/post/{post.id}").get_data(as_text=True)
        self.assertIn("#Flask", page)
        self.assertIn("#Python", page)

    def test_tag_shared_by_many_posts(self):
        (tag,) = self.make_tags("Flask")
        first = self.make_post(title="First", tags=[tag])
        second = self.make_post(title="Second", tags=[tag])
        self.assertEqual(set(tag.posts), {first, second})

    def test_user_posts_relation(self):
        post = self.make_post(user=self.other)
        self.assertEqual(self.other.posts, [post])
        self.assertEqual(self.author.posts, [])

    # US06 — 404
    def test_404_not_found(self):
        self.assertEqual(self.client.get("/post/999").status_code, 404)
        self.assertEqual(self.client.get("/post/999/update").status_code, 404)
        response = self.client.get("/nonexistent-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Сторінку не знайдено", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
