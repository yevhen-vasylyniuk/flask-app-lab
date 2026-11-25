from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SelectChoice, SubmitField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length

from app import db
from app.users.models import User

CATEGORY_CHOICES = [
    ("news", "Новини"),
    ("publication", "Публікація"),
    ("tech", "Технології"),
    ("other", "Інше"),
]


class PostForm(FlaskForm):
    title = StringField(
        "Заголовок",
        validators=[
            DataRequired(message="Вкажіть заголовок."),
            Length(max=150, message="Заголовок має бути не довшим за 150 символів."),
        ],
    )
    content = TextAreaField(
        "Текст поста",
        render_kw={"rows": 6},
        validators=[DataRequired(message="Напишіть текст поста.")],
    )
    enabled = BooleanField("Показувати пост на сайті", default=True)
    publish_date = DateTimeLocalField(
        "Дата публікації",
        format="%Y-%m-%dT%H:%M",
        default=datetime.now,
        validators=[DataRequired(message="Вкажіть дату й час публікації.")],
    )
    category = SelectField(
        "Категорія",
        choices=[SelectChoice(value, label) for value, label in CATEGORY_CHOICES],
        validators=[DataRequired(message="Оберіть категорію.")],
    )
    author_id = SelectField("Автор", coerce=int, validators=[DataRequired(message="Оберіть автора.")])
    submit = SubmitField("Зберегти")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Список авторів завантажуємо з БД (синтаксис SQLAlchemy 2.0)
        authors = db.session.scalars(db.select(User).order_by(User.id))
        self.author_id.choices = [SelectChoice(user.id, user.username) for user in authors]


class ConfirmDeleteForm(FlaskForm):
    """Форма підтвердження видалення (лише CSRF-токен і кнопка)."""
    submit = SubmitField("Так, видалити")
