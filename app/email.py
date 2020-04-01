from app import mail
from flask import current_app
from flask_mail import Message
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body=None, html_body=None):
    msg = Message(subject, sender=sender, recipients=recipients,
                  body=text_body, html=html_body)
    Thread(
        target=send_async_email,
        args=(
            current_app._get_current_object(),
            # extracts the actual application instance from inside the proxy object
            msg
        )
    ).start()
