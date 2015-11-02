from flask import jsonify

from ..models import Calendar
from . import api


@api.route('/calendars/')
def get_all_calendars():
    calendars = Calendar.query.all()
    return jsonify({'calendars': [c.to_json() for c in calendars]})


@api.route('/calendars/<int:id>/lessons/')
def get_calendar_lessons(id):
    calendar = Calendar.query.get_or_404(id)
    return jsonify({'lessons': [l.to_json() for l in calendar.lessons]})


@api.route('/calendars/<int:id>/courses/')
def get_calendar_courses(id):
    calendar = Calendar.query.get_or_404(id)
    return jsonify({'courses': [c.to_json() for c in calendar.courses.all()]})
