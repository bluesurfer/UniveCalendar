from itertools import groupby
from datetime import datetime

from flask.ext.login import current_user
from flask import jsonify, request

from ..models import User
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
        return jsonify({'error': 'invalid date format'})

    # Functions that adds URL and title of the course for this lesson.
    add_course_info = lambda l, url, title: l.update({'url': url, 'title': title}) or l
    lessons = [add_course_info(l.to_json(), c.url, '%s [%s]' % (c.name, c.code))
               for c in u.courses
               for l in c.calendar.lessons
               if l.start >= start and l.end <= end]
    return jsonify({'lessons': lessons})


@api.route('/users/<int:id>/classrooms/')
def get_user_classrooms(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    lessons = [l for c in u.courses for l in c.calendar.lessons]
    classrooms = set(c for l in lessons for c in l.classrooms)
    return jsonify({'classrooms': [c.to_json() for c in classrooms]})


@api.route('/users/<int:id>/locations/')
def get_user_locations(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    lessons = [l for c in u.courses for l in c.calendar.lessons]
    classrooms = set(c for l in lessons for c in l.classrooms)
    locations = []
    for location, group in groupby(classrooms, lambda c: c.location):
        json_loc = location.to_json()
        json_loc['classrooms'] = ', '.join(c.name for c in group)
        locations.append(json_loc)
    return jsonify({'locations': locations})
