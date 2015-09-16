from flask.ext.login import current_user
from flask import jsonify

from ..models import User, Feed

from . import api
from .errors import forbidden


@api.route('/users/<int:id>/courses/')
def get_user_courses(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    courses = u.courses.all()
    return jsonify({'courses': [c.to_json() for c in courses]})


@api.route('/users/<int:id>/lessons/')
def get_user_lessons(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    lessons = [l for c in u.courses.all() for l in c.lessons.all()]
    return jsonify({'lessons': [l.to_json() for l in lessons]})


@api.route('/users/<int:id>/feeds/')
def get_user_feeds(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    professors = set([c.professor for c in u.courses.all()])
    return jsonify({'feeds': [f.to_json() for p in professors
                              for f in p.feeds]})
