from flask import jsonify

from ..models import Course

from . import api


@api.route('/courses/')
def get_courses():
    courses = Course.query.all()
    return jsonify({'courses': [c.to_json() for c in courses]})


@api.route('/courses/<int:id>/lessons/')
def get_course_lessons(id):
    c = Course.query.get_or_404(id)
    lessons = c.lessons.all()
    return jsonify({'lessons': [l.to_json() for l in lessons]})


@api.route('/courses/<int:id>/users/')
def get_course_users(id):
    c = Course.query.get_or_404(id)
    users = c.users.all()
    return jsonify({'users': [u.to_json() for u in users]})

