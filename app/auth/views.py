from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required, \
    current_user
from flask.ext.babel import gettext, lazy_gettext
from flask.ext import breadcrumbs
from . import auth
from .forms import LoginForm, RegistrationForm, PasswordResetForm, \
    PasswordResetRequestForm, ChangePasswordForm, ChangeEmailForm
from ..email import send_email
from ..models import db, User


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(gettext('Invalid username or password.'), 'danger')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(gettext('Logout successful.'), 'info')
    return redirect(url_for('auth.login'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,
                   gettext('Confirm Your Account'),
                   'auth/email/en/confirm',
                   user=user,
                   token=token)
        flash(gettext('A confirmation email has been sent to you by email.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(gettext('You have confirmed your account. Thanks!'), 'info')
    else:
        flash(gettext('The confirmation link is invalid or has expired.'), 'danger')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,
               gettext('Confirm Your Account'),
               'auth/email/en/confirm',
               user=current_user,
               token=token)
    flash(gettext('A new confirmation email has been sent to you by email.'), 'success')
    return redirect(url_for('auth.login'))


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, gettext('Reset Your Password'),
                       'auth/email/en/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash(gettext('An email with instructions to reset your '
                      'password has been sent to you.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('auth.login'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('auth.login'))
        if user.reset_password(token, form.password.data):
            flash(gettext('Your password has been updated.'), 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(gettext('Password reset has failed.'), 'danger')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
@breadcrumbs.register_breadcrumb(auth, '.profile.change_password',
                                 lazy_gettext('Change Password'))
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(gettext('Your password has been updated.'), 'success')
            return redirect(url_for('main.index'))
        else:
            flash(gettext('Invalid password.'), 'danger')
    return render_template("auth/change_password.html", form=form)


@auth.route('/profile')
@login_required
@breadcrumbs.register_breadcrumb(auth, '.profile', lazy_gettext('Profile'))
def profile():
    return render_template('profile.html')


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
@breadcrumbs.register_breadcrumb(auth, '.profile.change_email',
                                 lazy_gettext('Change Email'))
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/en/change_email',
                       user=current_user, token=token)
            flash(gettext('An email with instructions to confirm your new email '
                  'address has been sent to you.'))
            return redirect(url_for('main.index'))
        else:
            flash(gettext('Invalid email or password.'))
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(gettext('Your email address has been updated.'))
    else:
        flash(gettext('Invalid request.'))
    return redirect(url_for('main.index'))


@auth.route('/activate-telegram')
@login_required
@breadcrumbs.register_breadcrumb(auth, '.profile.activate_telegram',
                                 lazy_gettext('Activate Telegram'))
def activate_telegram():
    token = current_user.generate_unique_code_token()
    return render_template('auth/activate_telegram.html',token=token)