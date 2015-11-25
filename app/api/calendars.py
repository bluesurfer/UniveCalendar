from flask import jsonify, request, current_app, url_for
from ..models import Calendar
from . import api


@api.route('/calendars/')
def get_calendars():
    page = request.args.get('page', 1, type=int)
    pagination = Calendar.query.paginate(
        page, per_page=current_app.config['OBJECTS_PER_PAGE'],
        error_out=False)
    calendars = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_calendars', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_calendars', page=page + 1, _external=True)
    return jsonify({
        'calendars': [cal.to_json() for cal in calendars],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/calendars/<int:id>')
def get_comment(id):
    cal = Calendar.query.get_or_404(id)
    return jsonify(cal.to_json())


@api.route('/calendars/<int:id>/lessons/')
def get_calendar_lessons(id):
    cal = Calendar.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = cal.lessons.paginate(
        page, per_page=current_app.config['OBJECTS_PER_PAGE'],
        error_out=False)
    lessons = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_calendar_lessons', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_calendar_lessons', page=page + 1, _external=True)
    return jsonify({
        'lessons': [l.to_json() for l in lessons],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/calendars/<int:id>/courses/')
def get_calendar_courses(id):
    cal = Calendar.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = cal.courses.paginate(
        page, per_page=current_app.config['OBJECTS_PER_PAGE'],
        error_out=False)
    lessons = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_calendar_courses', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_calendar_courses', page=page + 1, _external=True)
    return jsonify({
        'courses': [l.to_json() for l in lessons],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })