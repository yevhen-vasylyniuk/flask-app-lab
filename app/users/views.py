from flask import request, redirect, url_for, render_template, flash, session
from . import user_bp

# Заглушка замість бази даних: логін -> пароль
USERS = {
    "user1": "1234",
    "admin": "admin",
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


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if USERS.get(username) == password:
            session["username"] = username
            flash(f"Ви успішно увійшли як {username}!", "success")
            return redirect(url_for("users.profile"))

        flash("Невірний логін або пароль. Спробуйте ще раз!", "danger")
        return redirect(url_for("users.login"))

    return render_template("login.html", title="Вхід")


@user_bp.route("/profile")
def profile():
    username = session.get("username")
    if not username:
        flash("Спочатку увійдіть у систему!", "danger")
        return redirect(url_for("users.login"))

    return render_template("profile.html", title="Профіль", username=username,
                           cookies=request.cookies)


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
