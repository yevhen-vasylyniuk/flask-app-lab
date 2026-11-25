import logging
import os

from flask import request, render_template, redirect, url_for, flash
from . import app
from .forms import ContactForm, SUBJECTS

# Окремий логер, який дописує повідомлення з контактної форми у файл
os.makedirs(os.path.dirname(app.config["CONTACT_LOG"]), exist_ok=True)
contact_logger = logging.getLogger("contact_form")
contact_logger.setLevel(logging.INFO)
_handler = logging.FileHandler(app.config["CONTACT_LOG"], encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
contact_logger.addHandler(_handler)


@app.route('/')
def main():
    return render_template('resume.html', title='Резюме')


@app.route('/homepage')
def home():
    """View for the Home page of your website."""
    agent = request.user_agent
    return render_template('homepage.html', title='Головна', agent=agent)


@app.route('/resume')
def resume():
    return render_template('resume.html', title='Резюме')


@app.route('/contacts', methods=['GET', 'POST'])
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
            return redirect(url_for('contacts'))

        flash(f"Дякуємо, {form.name.data}! Повідомлення надіслано й збережено.", "success")
        # Post/Redirect/Get: після успішного POST перенаправляємо на GET
        return redirect(url_for('contacts'))

    if request.method == 'POST':
        flash("Повідомлення не надіслано. Виправте помилки у формі.", "danger")

    return render_template('contacts.html', title='Контакти', form=form)
