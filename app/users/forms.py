from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from app import db
from .models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        "Ім'я користувача",
        validators=[
            DataRequired(message="Вкажіть ім'я користувача."),
            Length(min=4, max=14, message="Ім'я має містити від 4 до 14 символів."),
            Regexp(
                r"^[A-Za-z][A-Za-z0-9_.]*$",
                message="Ім'я має починатися з літери й містити лише латинські літери, цифри, крапки або підкреслення.",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(message="Вкажіть email."), Email(message="Некоректна адреса email.")],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Вкажіть пароль."),
            Length(min=6, message="Пароль має містити щонайменше 6 символів."),
        ],
    )
    confirm_password = PasswordField(
        "Підтвердіть пароль",
        validators=[
            DataRequired(message="Повторіть пароль."),
            EqualTo("password", message="Паролі не збігаються."),
        ],
    )
    submit = SubmitField("Зареєструватися")

    def validate_username(self, field):
        if db.session.scalar(db.select(User).where(User.username == field.data)):
            raise ValidationError("Користувач з таким ім'ям уже існує.")

    def validate_email(self, field):
        if db.session.scalar(db.select(User).where(User.email == field.data)):
            raise ValidationError(f"Користувач з поштою {field.data} уже зареєстрований.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(message="Вкажіть email."), Email(message="Некоректна адреса email.")],
    )
    password = PasswordField("Пароль", validators=[DataRequired(message="Вкажіть пароль.")])
    remember = BooleanField("Запам'ятати мене")
    submit = SubmitField("Увійти")
