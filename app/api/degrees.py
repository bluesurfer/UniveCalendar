from flask import jsonify, request

from . import api
from ..models import Degree


@api.route('/degrees/')
def get_degrees():
    cat = request.args.get('cat', '')
    degrees = Degree.query.filter_by(category=cat) \
        if cat else Degree.query.all()
    return jsonify({'degrees': [d.to_json() for d in degrees]})


@api.route('/degrees/<int:id>/curriculums/')
def get_degree_curriculums(id):
    d = Degree.query.get_or_404(id)
    return jsonify({'curriculums': [c.to_json() for c in d.curriculums]})
