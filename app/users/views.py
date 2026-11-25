from urllib.parse import urlsplit

from flask import request, redirect, url_for, render_template, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from . import user_bp
from .forms import RegistrationForm, LoginForm
from .models import User

# Доступні кольорові схеми для сторінки профілю
THEMES = {
    "light": "Світла",
    "dark": "Темна",
}


@user_bp.route("/hi/<string:name>")   # /users/hi/ivan?age=45
def greetings(name):
    name = name.upper()
    age = request.args.get("age", None, int)

    return render_template("hi.html", title="Привітання", name=name, age=age)


@user_bp.route("/admin")
def admin():
    to_url = url_for("users.greetings", name="administrator", age=45, _external=True)
    print(to_url)
    return redirect(to_url)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=User.hash_password(form.password.data),
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Акаунт {user.username} створено! Тепер можна увійти.", "success")
        return redirect(url_for("users.login"))

    if request.method == "POST":
        flash("Реєстрацію не завершено. Виправте помилки у формі.", "danger")

    return render_template("register.html", title="Реєстрація", form=form)


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            session["username"] = user.username  # для сторінок, що читають ім'я із сесії
            flash(f"Вітаємо, {user.username}! Вхід успішний.", "success")
            # Повертаємо на сторінку, з якої перенаправили на вхід (лише локальні адреси)
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc:
                next_page = url_for("users.account")
            return redirect(next_page)

        flash("Невірний email або пароль. Спробуйте ще раз!", "danger")
        return redirect(url_for("users.login"))

    return render_template("login.html", title="Вхід", form=form)


@user_bp.route("/account")
@login_required
def account():
    return render_template("account.html", title="Акаунт", user=current_user)


@user_bp.route("/all")
@login_required
def users_list():
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return render_template("users_list.html", title="Користувачі", users=users)


@user_bp.route("/profile")
@login_required
def profile():
    theme = request.cookies.get("theme", "light")
    if theme not in THEMES:
        theme = "light"

    return render_template("profile.html", title="Профіль", username=current_user.username,
                           cookies=request.cookies, theme=theme)


@user_bp.route("/theme/<string:scheme>")
def set_theme(scheme):
    response = redirect(url_for("users.profile"))
    if scheme not in THEMES:
        flash("Невідома кольорова схема.", "warning")
        return response

    # Зберігаємо вибір на рік, щоб він діяв і при наступних відвідуваннях
    response.set_cookie("theme", scheme, max_age=60 * 60 * 24 * 365)
    flash(f"Кольорову схему змінено на «{THEMES[scheme]}».", "success")
    return response


@user_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.pop("username", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))


@user_bp.route("/cookies/add", methods=["POST"])
@login_required
def add_cookie():
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "")
    max_age = request.form.get("max_age", None, int)

    if not key:
        flash("Вкажіть ключ кукі.", "warning")
        return redirect(url_for("users.profile"))

    response = redirect(url_for("users.profile"))
    response.set_cookie(key, value, max_age=max_age)
    flash(f"Кукі «{key}» успішно додано.", "success")
    return response


@user_bp.route("/cookies/delete", methods=["POST"])
@login_required
def delete_cookie():
    key = request.form.get("key", "").strip()
    response = redirect(url_for("users.profile"))

    if key == "session":
        flash("Кукі сесії видаляти не можна, для цього є кнопка «Вийти».", "warning")
    elif key in request.cookies:
        response.delete_cookie(key)
        flash(f"Кукі «{key}» видалено.", "success")
    else:
        flash(f"Кукі «{key}» не знайдено.", "warning")
    return response


@user_bp.route("/cookies/delete_all", methods=["POST"])
@login_required
def delete_all_cookies():
    response = redirect(url_for("users.profile"))
    # Кукі сесії та «запам'ятати мене» залишаємо, інакше користувача буде розлогінено
    for key in request.cookies:
        if key not in ("session", "remember_token"):
            response.delete_cookie(key)
    flash("Усі кукі видалено.", "success")
    return response
