from flask import jsonify, request, current_app, url_for
from ..models import Course
from . import api


@api.route('/courses/')
def get_courses():
    page = request.args.get('page', 1, type=int)
    pagination = Course.query.order_by(Course.id.desc()).paginate(
        page, per_page=current_app.config['COURSES_PER_PAGE'],
        error_out=False)
    courses = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_courses', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_courses', page=page+1, _external=True)
    return jsonify({
        'posts': [course.to_json() for course in courses],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/courses/<int:id>')
def get_course(id):
    c = Course.query.get_or_404(id)
    return jsonify({'course': c.to_json()})


@api.route('/courses/<int:id>/users/')
def get_course_users(id):
    c = Course.query.get_or_404(id)
    return jsonify({'users': [u.to_json() for u in c.users]})
