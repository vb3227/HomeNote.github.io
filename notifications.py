from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# ======= Настройки почты =======
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vanya2010b@gmail.com'       # Ваша почта
app.config['MAIL_PASSWORD'] = 'jpsdbsvgkjqeykca'    # App Password

mail = Mail(app)

@app.route('/send-test')
def send_test_email():
    msg = Message(
        subject="Test Email",
        sender=app.config['MAIL_USERNAME'],
        recipients=['DIAB230336@diabstudents.com'],  # Кому отправляем
        body="Это тестовое письмо с Flask-Mail и Gmail App Password."
    )
    mail.send(msg)
    print("Письмо отправлено!")
    return "success"
    

if __name__ == '__main__':
    app.run(debug=True)
