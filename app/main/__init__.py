"""
Main blueprint
"""
from flask import Blueprint
from flask.ext import breadcrumbs

main = Blueprint('main', __name__)
breadcrumbs.default_breadcrumb_root(main, '.')

from . import views, errors
