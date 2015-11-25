"""
Migrate data from 'db_filename' to app database URL
"""
import datetime
import logging
import sqlite3

from app import models
from manage import app, db


logging.basicConfig(level=logging.INFO)
date_format = '%Y-%m-%d %H:%M:%S.%f'
db_filename = 'dump.sqlite'


def lesson_handler(row):
    res = dict(row)
    res['has_changed'] = bool(res['has_changed'])
    for f in ['start', 'end']:
        res[f] = datetime.datetime.strptime(res[f], date_format)
    return res


def user_handler(row):
    res = dict(row)
    res['confirmed'] = bool(res['confirmed'])
    for f in ['last_seen', 'member_since']:
        res[f] = datetime.datetime.strptime(res[f], date_format)
    return res


def feed_handler(row):
    res = dict(row)
    res['timestamp'] = datetime.datetime.strptime(res['timestamp'], date_format)
    return res


with sqlite3.connect(db_filename) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    with app.app_context():

        logging.info('Migrating "locations" ...')
        cursor.execute("SELECT * FROM locations")
        db.engine.execute(
            models.Location.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "classrooms" ...')
        cursor.execute("SELECT * FROM classrooms")
        db.engine.execute(
            models.Classroom.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "professors" ...')
        cursor.execute("SELECT * FROM professors")
        db.engine.execute(
            models.Professor.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "degrees" ...')
        cursor.execute("SELECT * FROM degrees")
        db.engine.execute(
            models.Degree.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "calendars" ...')
        cursor.execute("SELECT * FROM calendars")
        db.engine.execute(
            models.Calendar.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "courses" ...')
        cursor.execute("SELECT * FROM courses")
        db.engine.execute(
            models.Course.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "curriculums" ...')
        cursor.execute("SELECT * FROM curriculums")
        db.engine.execute(
            models.Curriculum.__table__.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "lessons" ...')
        cursor.execute("SELECT * FROM lessons")
        db.engine.execute(
            models.Lesson.__table__.insert(),
            [lesson_handler(row) for row in cursor.fetchall()])

        logging.info('Migrating "held_at" ...')
        cursor.execute("SELECT * FROM held_at")
        db.engine.execute(
            models.held_at.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "courses_curriculums" ...')
        cursor.execute("SELECT * FROM courses_curriculums")
        db.engine.execute(
            models.courses_curriculums.insert(),
            [dict(row) for row in cursor.fetchall()])

        logging.info('Migrating "feeds" ...')
        cursor.execute("SELECT * FROM feeds")
        db.engine.execute(
            models.Feed.__table__.insert(),
            [feed_handler(row) for row in cursor.fetchall()])

        logging.info('Migrating "users" ...')
        cursor.execute("SELECT * FROM users")
        db.engine.execute(
            models.User.__table__.insert(),
            [user_handler(row) for row in cursor.fetchall()])

        logging.info('Migrating "follows" ...')
        cursor.execute("SELECT * FROM follows")
        db.engine.execute(
            models.follows.insert(),
            [dict(row) for row in cursor.fetchall()])