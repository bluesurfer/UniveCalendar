import datetime

from flask.ext.login import current_user
from flask import jsonify, request
from sqlalchemy import or_

from ..models import User, Feed, Lesson
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
    return jsonify({'courses': [c.to_json() for c in u.courses.all()]})


@api.route('/users/<int:id>/lessons/')
def get_user_lessons(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    lessons = [l for c in u.courses for l in c.calendar.lessons.filter(
        Lesson.start >= datetime.datetime.today()).all()]
    return jsonify({'lessons': [l.to_json() for l in lessons]})


@api.route('/users/<int:id>/locations/')
def get_user_locations(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    locations = set([l.location for c in u.courses for l in c.calendar.lessons])
    return jsonify({'locations': [l.to_json() for l in locations]})


@api.route('/users/<int:id>/feeds/')
def get_user_feeds(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    professor_ids = set([c.professor_id for c in u.courses])
    lessons_ids = [l.id for c in u.courses for l in c.lessons]
    feeds = Feed.query.filter(
        or_(Feed.professor_id.in_(professor_ids),
            Feed.lesson_id.in_(lessons_ids))).all()
    return jsonify({'feeds': [f.to_json() for f in feeds]})
