from flask.ext.wtf import Form
from flask.ext.babel import gettext, lazy_gettext
from wtforms import StringField, TextAreaField, BooleanField, \
    SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional

from ..models import User


class EditProfileForm(Form):
    email = StringField(lazy_gettext('Change email'), validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    phone_number = StringField(lazy_gettext('Change phone number'), validators=[
        Optional(),
        Regexp('^(\d{3})-(\d{3})-(\d{4})$', 0, gettext('Invalid phone number.'))
    ])
    username = StringField(lazy_gettext('Change username'), validators=[
        DataRequired(),
        Length(6, 64, message=lazy_gettext('Username must have at least 6 characters')),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, gettext('Usernames must have only letters, '
                                                      'numbers, dots or underscores'))])
    notify_me = BooleanField(lazy_gettext('Notify feeds on Telegram'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username already in use'))
