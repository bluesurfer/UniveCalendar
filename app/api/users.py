from datetime import datetime

from flask.ext.login import current_user
from flask import jsonify, request
from sqlalchemy import and_

from ..models import User, Lesson
from . import api
from .errors import forbidden


@api.route('/users/<int:id>')
def get_user(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    return jsonify({'user': u.to_json()})


@api.route('/users/<int:id>/courses/')
def get_user_courses(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    return jsonify({'courses': [c.to_json() for c in u.courses]})


@api.route('/users/<int:id>/lessons/')
def get_user_lessons(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    try:
        start = datetime.strptime(request.args.get('start', ''), '%Y-%m-%d')
        end = datetime.strptime(request.args.get('end', ''), '%Y-%m-%d')
    except ValueError:
        lessons = [l for c in u.courses for l in c.calendar.lessons]
        return jsonify({'lessons': [l.to_json() for l in lessons]})
    lessons = [l for c in u.courses for l in c.calendar.lessons.filter(
        and_(Lesson.start >= start, Lesson.end <= end))]
    return jsonify({'lessons': [l.to_json() for l in lessons]})


@api.route('/users/<int:id>/locations/')
def get_user_locations(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    locations = set([l.location for c in u.courses for l in c.calendar.lessons])
    return jsonify({'locations': [l.to_json() for l in locations]})

