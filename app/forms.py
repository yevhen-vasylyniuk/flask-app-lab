from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectChoice, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp

SUBJECTS = [
    ("", "— Оберіть тему —"),
    ("cooperation", "Співпраця"),
    ("job", "Пропозиція роботи"),
    ("resume", "Питання щодо резюме"),
    ("other", "Інше"),
]


class ContactForm(FlaskForm):
    name = StringField(
        "Ім'я",
        validators=[
            DataRequired(message="Вкажіть ім'я."),
            Length(min=4, max=10, message="Ім'я має містити від 4 до 10 символів."),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Вкажіть email."),
            Email(message="Некоректна адреса email."),
        ],
    )
    phone = StringField(
        "Телефон",
        validators=[
            DataRequired(message="Вкажіть номер телефону."),
            Regexp(r"^\+380\d{9}$", message="Формат телефону: +380XXXXXXXXX."),
        ],
    )
    subject = SelectField(
        "Тема",
        choices=[SelectChoice(value, label) for value, label in SUBJECTS],
        validators=[DataRequired(message="Оберіть тему повідомлення.")],
    )
    message = TextAreaField(
        "Повідомлення",
        render_kw={"rows": 5},
        validators=[
            DataRequired(message="Напишіть повідомлення."),
            Length(max=500, message="Повідомлення має бути не довшим за 500 символів."),
        ],
    )
    submit = SubmitField("Надіслати")
