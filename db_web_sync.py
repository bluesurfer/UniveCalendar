"""
Synchronize application's database (data from web service).
"""
import os
import re
import json
import multiprocessing
import time
import datetime
import logging

from urllib2 import urlopen, HTTPError

from manage import app, db

FORMAT = ' %(levelname)s %(asctime)-15s PID:%(process)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT, filename='sync.log')
basedir = os.path.abspath(os.path.dirname(__file__))
re_avatar_url = re.compile(r'(\/media\/foto_persone&#x2F;\w&#x2F;.*(.jpg|.png|.jpeg))', flags=re.I)


def add_or_update(session, model, search_key=None, **kwargs):
    """ Add a model object to the database. If such object exists
    for a given search key then update it.

    """
    params = {search_key: kwargs[search_key]} \
        if search_key in kwargs.keys() else kwargs
    instance = session.query(model).filter_by(**params).first()
    if instance:
        logging.info('Updating "%s"' % model.__name__)
        for key, value in kwargs.iteritems():
            setattr(instance, key, value)
            session.merge(instance)
    else:
        logging.info('Adding "%s"' % model.__name__)
        instance = model(**kwargs)
        session.add(instance)
    session.commit()
    return instance


def merge_degrees(json_degrees):
    from app.models import Curriculum, Degree

    for (i, row) in enumerate(json_degrees):
        logging.info('Processing row %s of %s' % (i + 1, len(json_degrees)))
        degree = add_or_update(
            db.session, Degree, 'code',
            code=row['CDS_COD'],
            name=row['CDS_DES'],
            category_code=row['TIPO_CORSO_COD'],
            category_desc=row['TIPO_CORSO_DES']
        )
        add_or_update(
            db.session, Curriculum,
            code=row['PDS_COD'],
            name=row['PDS_DES'],
            degree=degree
        )


def merge_professors(json_professors):
    from app.models import Professor

    for (i, row) in enumerate(json_professors):
        logging.info('Processing row %s of %s with id %s' % (i + 1,
                                                             len(json_professors),
                                                             row['DOCENTE_ID']))
        add_or_update(
            db.session, Professor, 'id',
            id=row['DOCENTE_ID'],
            first_name=row['NOME'],
            last_name=row['COGNOME'],
            username=row['USERNAME'],
            avatar_url=get_professor_avatar_url(row['DOCENTE_ID']),
            email=row['MAIL'],
        )


def merge_courses(json_courses):
    from app.models import Course, Calendar

    for (i, row) in enumerate(json_courses):
        logging.info('Processing row %s of %s' % (i + 1, len(json_courses)))
        calendar = add_or_update(
            db.session, Calendar, 'id',
            id=row['AR_ID']
        )

        course = add_or_update(
            db.session, Course, 'id',
            id=row['AF_ID'],
            name=row['NOME'],
            code=row['CODICE'],
            period=row['CICLO'],
            credit=row['PESO'],
            total_credit=row['PESO_TOTALE'],
            year=row['ANNO_CORSO'],
            partition=row['PARTIZIONE'],
            field=row['SETTORE']
        )

        calendar.courses.append(course)
        db.session.commit()


def merge_lessons(json_lessons):
    from app.models import Lesson, Classroom

    date_format = '%Y-%m-%d%H:%M'
    for (i, row) in enumerate(json_lessons):
        logging.info('Processing row %s of %s' % (i + 1, len(json_lessons)))
        classroom = Classroom.query.filter_by(code=row['AULA_ID']).first()
        if classroom.location.address == 'Via Torino 155, 30170 Venezia Mestre':
            start = datetime.datetime.strptime(row['GIORNO'] + row['INIZIO'], date_format)
            end = datetime.datetime.strptime(row['GIORNO'] + row['FINE'], date_format)
            lesson = add_or_update(
                db.session, Lesson,
                start=start,
                end=end,
                description=row['DOCENTI'],
                calendar_id=row['AR_ID'],
            )
            lesson.classrooms.append(classroom)
            db.session.commit()
        else:
            logging.warning('Classroom not found')


def merge_classrooms(json_classrooms):
    from app.models import Classroom, Location

    for (i, row) in enumerate(json_classrooms):
        logging.info('Processing row %s of %s' % (i + 1, len(json_classrooms)))
        location = Location.query.filter_by(code=row['SEDE_ID']).first()
        if location:
            classroom = add_or_update(
                db.session, Classroom,
                code=row['AULA_ID'],
                name=row['NOME'],
                capacity=row['POSTI']
            )
            location.classrooms.append(classroom)
            db.session.commit()
        else:
            logging.warning('Location not found')


def merge_locations(json_locations):
    from app.models import Location

    for (i, row) in enumerate(json_locations):
        logging.info('Processing row %s of %s' % (i + 1, len(json_locations)))
        lng, lat, polyline = None, None, None
        if row['COORDINATE']:
            lng, lat, polyline = row['COORDINATE'].split(',')
        add_or_update(
            db.session, Location,
            code=row['SEDE_ID'],
            name=row['NOME'],
            address=row['INDIRIZZO'],
            lat=lat,
            lng=lng,
            polyline=polyline,
        )


def get_professor_avatar_url(prof_id):
    url = 'http://www.unive.it/data/persone/%s' % prof_id
    try:
        avatar = re_avatar_url.search(urlopen(url).read())
    except HTTPError as e:
        logging.warning('HTTP error')
        return
    return 'http://www.unive.it' + avatar.group(0).replace('&#x2F;', '/') if avatar else None


def courses_professors(json_relation):
    from app.models import Course, Professor

    for (i, row) in enumerate(json_relation):
        logging.info('Processing row %s of %s' % (i + 1, len(json_relation)))
        course = Course.query.get(row['AF_ID'])
        professor = Professor.query.get(row['DOCENTE_ID'])
        if course and professor:
            professor.courses.append(course)
            db.session.commit()
        else:
            logging.warning('Instance not found')


def courses_curriculums(json_relation):
    from app.models import Course, Curriculum, Degree

    for (i, row) in enumerate(json_relation):
        logging.info('Processing row %s of %s' % (i + 1, len(json_relation)))
        course = Course.query.get(row['AF_ID'])
        degree = Degree.query.filter_by(code=row['CDS_COD']).first()
        curriculum = Curriculum.query.filter_by(
            code=row['PDS_COD'], degree=degree).first()
        if course and curriculum:
            curriculum.courses.append(course)
            db.session.commit()
        else:
            logging.warning('Instance not found')


def parallel(worker, data, n_process):
    """Split data into evenly size slices and dispatch each one to
    a different process.

    """
    if n_process <= 1:
        return worker(data)

    step = len(data) / n_process
    jobs = []
    for i in xrange(0, len(data), step):
        p = multiprocessing.Process(
            target=worker, args=(data[i:i + step],))
        jobs.append(p)

    for p in jobs:
        p.start()

    for p in jobs:
        p.join()


if __name__ == '__main__':
    n_process = 2
    baseurl = 'http://static.unive.it/sitows/didattica/'
    start = time.time()

    with app.app_context():

        print('# Merging professors')
        json_professors = json.load(urlopen((baseurl + 'docenti')))
        parallel(merge_professors, json_professors, n_process)
        exit()

        print('# Merging locations')
        json_locations = json.load(urlopen((baseurl + 'sedi')))
        parallel(merge_locations, json_locations, n_process)

        print('# Merging classrooms')
        json_classrooms = json.load(urlopen((baseurl + 'aule')))
        parallel(merge_classrooms, json_classrooms, n_process)

        print('# Merging professors')
        json_professors = json.load(urlopen((baseurl + 'docenti')))
        parallel(merge_professors, json_professors, n_process)

        print('# Merging degrees and curriculums')
        json_degrees = json.load(urlopen((baseurl + 'corsi')))
        parallel(merge_degrees, json_degrees, n_process)

        print('# Merging courses')
        json_courses = json.load(urlopen((baseurl + 'insegnamenti')))
        parallel(merge_courses, json_courses, n_process)

        print('# Merging lessons')
        json_lessons = json.load(urlopen((baseurl + 'lezioni')))
        parallel(merge_lessons, json_lessons, n_process)

        print('# Merging courses/curriculums')
        json_relation = json.load(urlopen((baseurl + 'corsiinsegnamenti')))
        parallel(courses_curriculums, json_relation, n_process)

        print('# Merging courses/professors')
        json_relation = json.load(urlopen((baseurl + 'insegnamentidocenti')))
        parallel(courses_professors, json_relation, n_process)

    print('Done in %s secs (~%s min)' % (time.time() - start, (time.time() - start) / 60))
