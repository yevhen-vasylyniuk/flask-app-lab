import logging

from flask import Blueprint, request, render_template, redirect, url_for, flash
from .forms import ContactForm, SUBJECTS

main_bp = Blueprint("main", __name__)

# Обробник у файл додається в create_app (configure_contact_logger)
contact_logger = logging.getLogger("contact_form")


@main_bp.route('/')
def index():
    return render_template('resume.html', title='Резюме')


@main_bp.route('/homepage')
def home():
    """View for the Home page of your website."""
    agent = request.user_agent
    return render_template('homepage.html', title='Головна', agent=agent)


@main_bp.route('/resume')
def resume():
    return render_template('resume.html', title='Резюме')


@main_bp.route('/contacts', methods=['GET', 'POST'])
def contacts():
    form = ContactForm()
    if form.validate_on_submit():
        subject = dict(SUBJECTS)[form.subject.data]
        try:
            contact_logger.info(
                "name=%s | email=%s | phone=%s | subject=%s | message=%s",
                form.name.data, form.email.data, form.phone.data,
                subject, form.message.data.replace("\n", " "),
            )
        except OSError:
            flash("Не вдалося зберегти повідомлення. Спробуйте пізніше.", "danger")
            return redirect(url_for('main.contacts'))

        flash(f"Дякуємо, {form.name.data}! Повідомлення надіслано й збережено.", "success")
        # Post/Redirect/Get: після успішного POST перенаправляємо на GET
        return redirect(url_for('main.contacts'))

    if request.method == 'POST':
        flash("Повідомлення не надіслано. Виправте помилки у формі.", "danger")

    return render_template('contacts.html', title='Контакти', form=form)
