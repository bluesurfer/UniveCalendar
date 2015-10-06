from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, TextAreaField, BooleanField, \
    SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional

from ..models import User


class EditProfileForm(Form):
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    phone_number = StringField('Phone Number', validators=[
        Optional(),
        Regexp('^(?:\+?44)?[07]\d{9,13}$'), 0, gettext('Not a valid phone number')])

    username = StringField('Username', validators=[
        DataRequired(),
        Length(6, 64, message=gettext('Username must have at least 6 characters')),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, gettext('Usernames must have only letters, '
                                                      'numbers, dots or underscores'))])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username already in use'))
