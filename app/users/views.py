from flask import request, redirect, url_for, render_template, flash, session

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
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            session["username"] = user.username
            flash(f"Вітаємо, {user.username}! Вхід успішний.", "success")
            return redirect(url_for("users.account"))

        flash("Невірний email або пароль. Спробуйте ще раз!", "danger")
        return redirect(url_for("users.login"))

    return render_template("login.html", title="Вхід", form=form)


@user_bp.route("/account")
def account():
    username = session.get("username")
    user = db.session.scalar(db.select(User).where(User.username == username)) if username else None
    if not user:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))
    return render_template("account.html", title="Акаунт", user=user)


@user_bp.route("/all")
def users_list():
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return render_template("users_list.html", title="Користувачі", users=users)


@user_bp.route("/profile")
def profile():
    username = session.get("username")
    if not username:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))

    theme = request.cookies.get("theme", "light")
    if theme not in THEMES:
        theme = "light"

    return render_template("profile.html", title="Профіль", username=username,
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
def logout():
    session.pop("username", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))


@user_bp.route("/cookies/add", methods=["POST"])
def add_cookie():
    if "username" not in session:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))

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
def delete_cookie():
    if "username" not in session:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))

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
def delete_all_cookies():
    if "username" not in session:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))

    response = redirect(url_for("users.profile"))
    # Кукі сесії залишаємо, інакше користувача буде розлогінено
    for key in request.cookies:
        if key != "session":
            response.delete_cookie(key)
    flash("Усі кукі видалено.", "success")
    return response
