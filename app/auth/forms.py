from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, \
    ValidationError, EqualTo, Optional
from flask.ext.babel import gettext

from ..models import User


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField(gettext('Keep me logged in'))
    submit = SubmitField('Log In')


class RegistrationForm(Form):
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
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(6, 64, message=gettext('Password must have at least 6 characters')),
        EqualTo('password2', message=gettext('Passwords must match'))])
    password2 = PasswordField(gettext('Confirm password'), validators=[DataRequired()])
    submit = SubmitField(gettext('Register'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username already in use'))


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('password2', message=gettext('Passwords must match'))])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(gettext('Unknown email address'))
