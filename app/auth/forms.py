from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(_l("Repeat Password"), validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField(_l("Register"))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_("Please use a different username."))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_("Please use an email address."))


class LoginForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember Me"))
    submit = SubmitField(_l("Sign In"))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Reset Password"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("New Password"), validators=[DataRequired()])
    password2 = PasswordField(_l("Repeat Password"), validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField(_l("Reset Password"))
