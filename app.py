from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('resume.html', title='Резюме')

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

if __name__ == '__main__':
    app.run(debug=True)