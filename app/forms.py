from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms.widgets import TextArea
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

class EditProfileForm(FlaskForm):
    username = StringField(_l("New username"), validators=[Length(0, 60)])
    about_me = StringField(_l("About me"), validators=[Length(0, 140)], widget=TextArea())
    submit = SubmitField(_l("Submit"))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(_("Username already exists. Please use a different username."))

class PostForm(FlaskForm):
    post = StringField(_l("Say something"), validators=[DataRequired(), Length(0, 140)], \
                       widget=TextArea(), render_kw={"class": "post-field"})
    submit = SubmitField(_l("Submit"))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Reset Password"))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("New Password"), validators=[DataRequired()])
    password2 = PasswordField(_l("Repeat Password"), validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField(_l("Reset Password"))
