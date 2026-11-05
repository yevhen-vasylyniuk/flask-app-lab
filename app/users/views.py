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

    return render_template("profile.html", title="Профіль", username=username)


@user_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))
