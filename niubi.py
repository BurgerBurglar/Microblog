from flask_mail import Message
from app import mail, app
from app.email import send_password_reset_email
from app.models import User

def send_email(subject, sender, recipients, text_body=None, html_body=None):
    with app.app_context():
        msg = Message(subject, sender=sender, recipients=recipients,
                    body=text_body, html=html_body)
        mail.send(msg)

if __name__ == "__main__":
    u = User.query.filter_by(username="田硕").first()
    if u:
        send_password_reset_email(u)
# from flask_mail import Message
# from app import mail, app
# with app.app_context():
#     msg = Message('test subject', 
#     # sender=app.config['ADMINS'][0],
#     sender=("Shuo Tian", "robbiefields1996@gmail.com"),
#     recipients=['tianshuo1996@outlook.com']
# )
#     msg.body = 'text body'
#     msg.html = '<h1>HTML body</h1>'
#     mail.send(msg)