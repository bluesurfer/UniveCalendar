from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, \
    ValidationError, EqualTo, Optional
from flask.ext.babel import lazy_gettext, gettext

from ..models import User


class LoginForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    password = PasswordField('Password', validators=[
        DataRequired()])
    remember_me = BooleanField(lazy_gettext('Keep me logged in'))
    submit = SubmitField(lazy_gettext('Log In'))


class RegistrationForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    username = StringField(lazy_gettext('Username'), validators=[
        DataRequired(),
        Length(6, 64, message=lazy_gettext('Username must have at least 6 characters')),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, lazy_gettext('Usernames must have only letters, '
                                                           'numbers, dots or underscores'))])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(6, 64, message=lazy_gettext('Password must have at least 6 characters')),
        EqualTo('password2', message=lazy_gettext('Passwords must match'))])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[
        DataRequired()])
    submit = SubmitField(lazy_gettext('Register'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(gettext('Username already in use'))


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    submit = SubmitField(lazy_gettext('Reset Password'))


class PasswordResetForm(Form):
    email = StringField('Email', validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    password = PasswordField(lazy_gettext('New Password'), validators=[
        DataRequired(),
        Length(6, 64, message=lazy_gettext('Password must have at least 6 characters')),
        EqualTo('password2', message=lazy_gettext('Passwords must match'))])
    password2 = PasswordField(lazy_gettext('Confirm password'), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext('Reset Password'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(gettext('Unknown email address'))


class ChangePasswordForm(Form):
    old_password = PasswordField(lazy_gettext('Old password'), validators=[
        DataRequired()])
    password = PasswordField(lazy_gettext('New password'), validators=[
        DataRequired(),
        EqualTo('password2', message=lazy_gettext('Passwords must match'))])
    password2 = PasswordField(lazy_gettext('Confirm new password'), validators=[
        DataRequired()])
    submit = SubmitField(lazy_gettext('Update Password'))


class ChangeEmailForm(Form):
    email = StringField(lazy_gettext('New Email'), validators=[
        DataRequired(),
        Length(1, 64),
        Email()])
    password = PasswordField('Password', validators=[
        DataRequired()])
    submit = SubmitField(lazy_gettext('Update Email Address'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(gettext('Email already registered.'))
