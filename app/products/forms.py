from decimal import Decimal

from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (StringField, TextAreaField, DecimalField, SelectField, SelectChoice,
                     IntegerField, SubmitField)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError

CATEGORIES = [
    ("laptops", "Ноутбуки"),
    ("phones", "Смартфони"),
    ("pc", "Комп'ютери"),
    ("accessories", "Аксесуари"),
]


def two_decimal_places(form, field):
    if field.data is not None and field.data != field.data.quantize(Decimal("0.01")):
        raise ValidationError("Ціна може мати не більше двох знаків після коми.")


def max_image_size(form, field):
    # Ліміт беремо з конфігурації, щоб його можна було змінити в одному місці
    FileSize(max_size=current_app.config["MAX_IMAGE_SIZE"],
             message="Зображення завелике (максимум 2 МБ).")(form, field)


class ProductForm(FlaskForm):
    name = StringField(
        "Назва",
        validators=[
            DataRequired(message="Вкажіть назву товару."),
            Length(min=3, message="Назва має містити щонайменше 3 символи."),
        ],
    )
    content = TextAreaField(
        "Опис",
        render_kw={"rows": 5, "cols": 40},
        validators=[DataRequired(message="Додайте опис товару.")],
    )
    price = DecimalField(
        "Ціна, $",
        places=2,
        validators=[
            InputRequired(message="Вкажіть ціну."),
            NumberRange(min=Decimal("0.01"), message="Ціна має бути додатною."),
            two_decimal_places,
        ],
    )
    category = SelectField(
        "Категорія",
        choices=[SelectChoice("", "— Оберіть категорію —")]
                + [SelectChoice(value, label) for value, label in CATEGORIES],
        validators=[DataRequired(message="Оберіть категорію.")],
    )
    quantity = IntegerField(
        "Кількість, шт.",
        validators=[
            InputRequired(message="Вкажіть кількість."),
            NumberRange(min=0, message="Кількість не може бути від'ємною."),
        ],
    )
    image = FileField(
        "Зображення (PNG, JPG, JPEG, до 2 МБ)",
        validators=[
            FileAllowed(["png", "jpg", "jpeg"], "Дозволені лише зображення PNG, JPG або JPEG."),
            max_image_size,
        ],
    )
    submit = SubmitField("Зберегти")


class DeleteForm(FlaskForm):
    """Порожня форма лише для CSRF-захисту запиту на видалення."""
    submit = SubmitField("Видалити")
