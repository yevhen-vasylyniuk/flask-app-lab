import os
import uuid

from flask import render_template, abort, flash, redirect, url_for, request, current_app
from werkzeug.exceptions import RequestEntityTooLarge

from . import products_bp, db
from .forms import ProductForm, DeleteForm, CATEGORIES


@products_bp.context_processor
def inject_categories():
    return {"category_names": dict(CATEGORIES)}


def _image_path(relative_path):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(relative_path))


def _with_image_url(product):
    """Додає image_url, якщо файл зображення справді існує."""
    image = product.get("image")
    product["image_url"] = None
    if image and os.path.exists(_image_path(image)):
        product["image_url"] = url_for("products.static", filename=image)
    return product


def _save_image(file):
    # Безпечне ім'я файлу: UUID + оригінальне розширення
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return f"uploads/{filename}"


def _delete_image(relative_path):
    if relative_path:
        path = _image_path(relative_path)
        if os.path.exists(path):
            os.remove(path)


def _form_data(form):
    return {
        "name": form.name.data.strip(),
        "content": form.content.data.strip(),
        "price": float(form.price.data),
        "category": form.category.data,
        "quantity": form.quantity.data,
    }


def _get_product_or_404(id):
    product = db.get_by_id(id)
    if product is None:
        abort(404)
    return product


@products_bp.errorhandler(404)
def product_not_found(error):
    return render_template("product_not_found.html", title="Товар не знайдено"), 404


@products_bp.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    flash("Файл завеликий. Максимальний розмір запиту — 5 МБ.", "danger")
    return redirect(request.url)


@products_bp.route("")
def get_products():
    products = [_with_image_url(p) for p in db.get_all()]
    return render_template("products.html", title="Товари", products=products)


@products_bp.route("/<int:id>")
def detail_product(id):
    product = _with_image_url(_get_product_or_404(id))
    return render_template("detail_product.html", title=product["name"],
                           product=product, delete_form=DeleteForm())


@products_bp.route("/add", methods=["GET", "POST"])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        data = _form_data(form)
        data["image"] = _save_image(form.image.data) if form.image.data else None
        product_id = db.create(data)
        flash(f"Товар «{data['name']}» успішно додано.", "success")
        return redirect(url_for("products.detail_product", id=product_id))

    if request.method == "POST":
        flash("Товар не додано. Виправте помилки у формі.", "danger")

    return render_template("product_form.html", title="Новий товар",
                           form=form, heading="Додати товар")


@products_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_product(id):
    product = _with_image_url(_get_product_or_404(id))
    form = ProductForm(data=product if request.method == "GET" else None)

    if form.validate_on_submit():
        data = _form_data(form)
        if form.image.data:
            # Нове зображення замінює старе, інакше залишаємо попереднє
            data["image"] = _save_image(form.image.data)
            _delete_image(product.get("image"))
        db.update(id, data)
        flash(f"Товар «{data['name']}» оновлено.", "success")
        return redirect(url_for("products.detail_product", id=id))

    if request.method == "POST":
        flash("Зміни не збережено. Виправте помилки у формі.", "danger")

    return render_template("product_form.html", title="Редагування товару",
                           form=form, heading=f"Редагувати «{product['name']}»", product=product)


@products_bp.route("/<int:id>/delete", methods=["POST"])
def delete_product(id):
    product = _get_product_or_404(id)
    if not DeleteForm().validate_on_submit():
        flash("Не вдалося видалити товар: недійсний запит.", "danger")
        return redirect(url_for("products.detail_product", id=id))

    db.delete(id)
    _delete_image(product.get("image"))
    flash(f"Товар «{product['name']}» видалено.", "success")
    return redirect(url_for("products.get_products"))
