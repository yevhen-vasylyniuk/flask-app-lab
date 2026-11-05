from flask import request, redirect, url_for, render_template
from . import user_bp


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
