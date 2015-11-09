from flask import jsonify
from ..models import Location
from . import api


@api.route('/locations/')
def get_locations():
    locations = Location.query.all()
    return jsonify({'locations': [l.to_json() for l in locations]})


@api.route('/locations/<int:id>/lessons')
def get_locations_courses(id):
    location = Location.query.get_or_404(id)
    return jsonify({'lessons': [l.to_json() for l in location.lessons]})