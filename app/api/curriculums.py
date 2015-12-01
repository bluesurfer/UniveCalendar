from sqlalchemy import or_

from flask import jsonify, request
from . import api
from ..models import Curriculum, Course


@api.route('/curriculums/')
def get_curriculums():
    curriculums = Curriculum.query.all()
    return jsonify({'curriculums': [c.to_json() for c in curriculums]})


@api.route('/curriculums/<int:id>/table/courses/')
def get_curriculum_courses(id):
    c = Curriculum.query.get_or_404(id)
    limit = min(request.args.get('limit', 5, type=int), 20)
    offset = request.args.get('offset', 0, type=int)
    sort = request.args.get('sort', 'id', type=str)
    descending = request.args.get('order', 'asc', type=str) == 'desc'
    search = request.args.get('search', '', type=str)
    column = sort if sort in Course.__sortable__ else 'id'
    query = c.courses

    if search:
        query = query.filter(or_(
            Course.name.like('%' + search + '%'),
            Course.code.like('%' + search + '%')))

    if descending:
        query = query.order_by(column + ' desc')
    else:
        query = query.order_by(column + ' asc')

    return jsonify({'total': query.count(),
                    'rows': [c.to_json() for c in query[offset:limit + offset]]})


