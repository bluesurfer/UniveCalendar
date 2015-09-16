from flask import jsonify

from ..models import Professor

from . import api


@api.route('/professors/')
def get_professors():
    profs = Professor.query.all()
    return jsonify({'professors': [p.to_json() for p in profs]})


@api.route('/professors/<int:id>/feeds/')
def get_professor_feeds(id):
    p = Professor.query.get_or_404(id)
    feeds = p.feeds.all()
    return jsonify({'feeds': [f.to_json() for f in feeds]})


@api.route('/professors/<int:id>/courses/')
def get_professor_courses(id):
    p = Professor.query.get_or_404(id)
    courses = p.courses.all()
    return jsonify({'courses': [c.to_json() for c in courses]})
