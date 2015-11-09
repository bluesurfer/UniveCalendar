from flask import jsonify
from . import api
from ..models import Curriculum


@api.route('/curriculums/')
def get_curriculums():
    curriculums = Curriculum.query.all()
    return jsonify({'curriculums': [c.to_json() for c in curriculums]})


@api.route('/curriculums/<int:id>/courses/')
def get_curriculum_courses(id):
    curriculum = Curriculum.query.get(id)
    return jsonify({'courses': [c.to_json() for c in curriculum.courses]})
