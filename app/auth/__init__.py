from flask import Blueprint
from flask.ext import breadcrumbs

auth = Blueprint('auth', __name__)
breadcrumbs.default_breadcrumb_root(auth, '.')

from . import views
