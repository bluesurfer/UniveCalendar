from flask import jsonify
from . import api
from ..models import Curriculum


@api.route('/curriculums/')
def get_all_curriculums():
    curriculums = Curriculum.query.all()
    return jsonify({'curriculums': [c.to_json() for c in curriculums]})


@api.route('/curriculums/<int:id>/courses/')
def get_curriculum_courses(id):
    cur = Curriculum.query.get(id)
    courses = [c.to_json() for c in cur.courses]
    return jsonify({'courses': courses,
                    'count': len(courses)})
