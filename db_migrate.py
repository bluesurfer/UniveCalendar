import datetime
import sqlite3

from app import models
from manage import app, db


db_filename = 'dump.sqlite'


def convert_to_datetime(row):
    format = '%Y-%m-%d %H:%M:%S.000000'
    result = dict(row)
    result['start'] = datetime.datetime.strptime(row['start'], format)
    result['end'] = datetime.datetime.strptime(row['end'], format)
    return result


with sqlite3.connect(db_filename) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    with app.app_context():
        cursor.execute("SELECT * FROM professors")
        db.engine.execute(
            models.Professor.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        cursor.execute("SELECT * FROM degrees")
        db.engine.execute(
            models.Degree.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        cursor.execute("SELECT * FROM curriculums")
        db.engine.execute(
            models.Curriculum.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        cursor.execute("SELECT * FROM calendars")
        db.engine.execute(
            models.Calendar.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        cursor.execute("SELECT * FROM lessons")
        db.engine.execute(
            models.Lesson.__table__.insert(),
            [convert_to_datetime(row) for row in cursor.fetchall()])

        cursor.execute("SELECT * FROM courses")
        db.engine.execute(
            models.Course.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

