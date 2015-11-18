from flask import jsonify
from ..models import Classroom
from . import api


@api.route('/classrooms/')
def get_classrooms():
    classrooms = Classroom.query.all()
    return jsonify({'classrooms': [c.to_json() for c in classrooms]})

