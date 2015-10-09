from flask.ext.wtf import Form
from flask_login import current_user
from flask.ext.babel import gettext, lazy_gettext
from wtforms import StringField, TextAreaField, BooleanField, \
    SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional

from ..models import User


class EditProfileForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    username = StringField(lazy_gettext('Username'), validators=[
        DataRequired(),
        Length(6, 64, message=lazy_gettext('Username must have at least 6 characters')),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, lazy_gettext('Usernames must have only letters, '
                                                           'numbers, dots or underscores'))])
    submit = SubmitField(lazy_gettext('Update Profile'))

    def validate_email(self, field):
        if current_user.email != field.data and User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered'))

    def validate_username(self, field):
        if current_user.username != field.data and User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username already in use'))
