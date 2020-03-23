from app import mail, app
from flask import render_template
from flask_mail import Message
from flask_babel import _
from app.models import User
from threading import Thread

def send_async_email(mail, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body=None, html_body=None):
    msg = Message(subject, sender=sender, recipients=recipients,
                body=text_body, html=html_body)
    Thread(target=send_async_email, args=(mail, msg)).start()

def send_password_reset_email(recipient):
    email_data = {
        "subject": _("Reset your password on Microblog"),
        "sender": ("Microblog team", "no-reply@mircroblog.com"),
        "recipients": [recipient.email],
        "html_body": render_template("email/reset_password.html", \
                                     user=recipient, \
                                     token=recipient.get_reset_password_token())
    }
    send_email(**email_data)

if __name__ == "__main__":
    # send_email("test", ("Shuo Tian", "robbiefields1996@gmail.com"),
    #            ["tianshuo1996@outlook.com"], "test")
    u = User.query.filter_by(username="田硕").first()
    if u:
        send_password_reset_email(u)