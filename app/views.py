from flask import request, render_template
from . import app


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
    sent = False
    if request.method == 'POST':
        # Заглушка: дані нікуди не надсилаються
        sent = True
    return render_template('contacts.html', title='Контакти', sent=sent)
