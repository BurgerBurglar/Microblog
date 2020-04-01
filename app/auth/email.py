from app.email import send_email
from flask import render_template
from flask_babel import _


def send_password_reset_email(recipient):
    email_data = {
        "subject": _("Reset your password on Microblog"),
        "sender": ("Microblog team", "no-reply@mircroblog.com"),
        "recipients": [recipient.email],
        "html_body": render_template("email/reset_password.html",
                                     user=recipient,
                                     token=recipient.get_hash_token())
    }
    send_email(**email_data)


def send_register_confirmation_email(recipient):
    email_data = {
        "subject": _("Welcome to Microblog"),
        "sender": ("Microblog team", "no-reply@mircroblog.com"),
        "recipients": [recipient.email],
        "html_body": render_template("email/confim_registration.html",
                                     user=recipient,
                                     token=recipient.get_hash_token())
    }
    send_email(**email_data)
