from itertools import groupby

from sqlalchemy import or_, inspect

from flask.ext.login import current_user
from flask import jsonify, request

from ..models import User, Course
from . import api
from .errors import forbidden


@api.route('/users/<int:id>')
def get_user(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')
    return jsonify({'user': u.to_json()})


@api.route('/users/<int:id>/table/courses/')
def get_user_courses(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    limit = min(request.args.get('limit', 5, type=int), 20)
    offset = request.args.get('offset', 0, type=int)
    sort = request.args.get('sort', 'id', type=str)
    descending = request.args.get('order', 'asc', type=str) == 'desc'
    search = request.args.get('search', '', type=str)
    column = sort if sort in Course.__sortable__ else 'id'

    if search:
        query = u.courses.filter(or_(
            Course.name.like('%' + search + '%'),
            Course.code.like('%' + search + '%')))
    else:
        query = u.courses

    if descending:
        query = query.order_by(column + ' desc')
    else:
        query = query.order_by(column + ' asc')

    return jsonify({'total': query.count(),
                    'rows': [c.to_json() for c in query[offset:limit + offset]]})


@api.route('/users/<int:id>/lessons/')
def get_user_lessons(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    start = request.args.get('start', '')
    end = request.args.get('end', '')
    lessons = [l.to_json(url=c.url, title=str(c))
               for c in u.courses
               for l in c.calendar.lessons_between(start, end)]

    return jsonify({'lessons': lessons})


@api.route('/users/<int:id>/classrooms/')
def get_user_classrooms(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    classrooms = set(classroom
                     for course in u.courses
                     for lesson in course.calendar.lessons
                     for classroom in lesson.classrooms)

    return jsonify({'classrooms': [c.to_json() for c in classrooms]})


@api.route('/users/<int:id>/locations/')
def get_user_locations(id):
    u = User.query.get_or_404(id)
    if current_user.id != u.id:
        return forbidden('Insufficient permissions')

    classrooms = set(classroom
                     for course in u.courses
                     for lesson in course.calendar.lessons
                     for classroom in lesson.classrooms)

    locations = []
    for location, group in groupby(classrooms, lambda c: c.location):
        json_loc = location.to_json()
        json_loc['classrooms'] = ', '.join(c.name for c in group)
        locations.append(json_loc)

    return jsonify({'locations': locations})
