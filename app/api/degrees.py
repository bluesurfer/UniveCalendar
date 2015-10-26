from flask import jsonify, request
from . import api
from ..models import Degree


@api.route('/degrees/')
def get_degrees_by_category():
    cat = request.args.get('cat', '0')
    degrees = Degree.query.filter_by(category=cat)
    return jsonify({'degrees': [d.to_json() for d in degrees]})


@api.route('/degrees/<int:id>/curriculums/')
def get_degree_curriculums(id):
    d = Degree.query.get_or_404(id)
    return jsonify({'curriculums': [c.to_json() for c in d.curriculums]})
