from flask import Blueprint

api = Blueprint('api', __name__)

from . import degrees, courses, professors, users, \
    curriculums, calendars, locations, errors