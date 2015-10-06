from flask import jsonify, request

from . import api

from ..models import Degree


@api.route('/degrees/')
def get_degrees():
    cat = request.args.get('cat', '0')
    degrees = Degree.query.filter_by(category=cat)
    return jsonify({'degrees': [d.to_json() for d in degrees]})


@api.route('/degrees/<int:id>/courses/')
def get_degree_courses(id):
    d = Degree.query.get_or_404(id)
    return jsonify({'courses': [c.to_json() for c in d.courses.all()]})
