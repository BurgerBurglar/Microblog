from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Length
from wtforms.widgets import TextArea
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l("New username"), validators=[Length(0, 60)], render_kw={'readonly': True})
    gender = SelectField(_l("Gender"), choices=[('M', _l("Male")), ('F', _l('Female')), ('B', _l('Bot'))])
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
    post = StringField(_l("Say something"), validators=[DataRequired(), Length(0, 140)],
                       widget=TextArea(), render_kw={"class": "post-field"})
    submit = SubmitField(_l("Submit"))
