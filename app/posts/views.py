from flask import render_template, redirect, url_for, flash, request, session

from app import db
from . import post_bp
from .forms import PostForm, ConfirmDeleteForm, CATEGORY_CHOICES
from .models import Post
from app.users.models import User


@post_bp.context_processor
def inject_categories():
    return {"category_names": dict(CATEGORY_CHOICES)}


@post_bp.route("")
def get_posts():
    stmt = db.select(Post).where(Post.is_active).order_by(Post.posted.desc())
    posts = db.session.scalars(stmt).all()
    return render_template("posts.html", title="Пости", posts=posts)


@post_bp.route("/create", methods=["GET", "POST"])
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            posted=form.publish_date.data,
            category=form.category.data,
            is_active=form.enabled.data,
            # Автор — користувач із сесії, якщо він є в БД
            user=db.session.scalar(db.select(User).where(User.username == session.get("username"))),
        )
        db.session.add(post)
        db.session.commit()
        flash("Пост успішно додано.", "success")
        return redirect(url_for("posts.get_posts"))

    if request.method == "POST":
        flash("Пост не додано. Виправте помилки у формі.", "danger")

    return render_template("add_post.html", title="Новий пост", form=form, heading="Новий пост")


@post_bp.route("/<int:id>")
def detail_post(id):
    post = db.get_or_404(Post, id)
    return render_template("detail_post.html", title=post.title, post=post)


@post_bp.route("/<int:id>/update", methods=["GET", "POST"])
def update_post(id):
    post = db.get_or_404(Post, id)
    form = PostForm(obj=post)

    if request.method == "GET":
        # Назви полів форми і моделі різні, тому ці два поля заповнюємо вручну
        form.publish_date.data = post.posted
        form.enabled.data = post.is_active

    if form.validate_on_submit():
        form.populate_obj(post)
        post.posted = form.publish_date.data
        post.is_active = form.enabled.data
        db.session.commit()
        flash("Пост успішно оновлено.", "success")
        return redirect(url_for("posts.detail_post", id=post.id))

    if request.method == "POST":
        flash("Зміни не збережено. Виправте помилки у формі.", "danger")

    return render_template("add_post.html", title="Редагування поста", form=form,
                           heading="Редагування поста", post=post)


@post_bp.route("/<int:id>/delete", methods=["GET", "POST"])
def delete_post(id):
    post = db.get_or_404(Post, id)
    form = ConfirmDeleteForm()

    if form.validate_on_submit():
        db.session.delete(post)
        db.session.commit()
        flash(f"Пост видалено: «{post.title}».", "success")
        return redirect(url_for("posts.get_posts"))

    return render_template("delete_confirm.html", title="Видалення поста", post=post, form=form)
