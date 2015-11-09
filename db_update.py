import os
import csv
import json
import argparse
import logging
import hashlib

from urllib2 import urlopen, HTTPError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, literal

from app import models
from manage import app, db

logging.basicConfig(level=logging.INFO, filename='db.log')

basedir = os.path.abspath(os.path.dirname(__file__))


def update_locations(args):
    logging.info('Reading data source "%s"' % args.datapath)
    with open(args.datapath, 'rt') as csvfile:
        reader = csv.DictReader(csvfile)
        with app.app_context():
            for row in reader:
                logging.info('Processing row %s' % reader.line_num)
                lng, lat = row['GOOGLE_SEDE'].split(',')[:2]
                location = models.Location(code=row['ID'],
                                           name=row['NOME'].decode('utf8'),
                                           lat=lat, lng=lng)
                db.session.add(location)
                try:
                    db.session.commit()
                    logging.info('Location added.')
                except IntegrityError as e:
                    logging.warn(e.message)
                    db.session.rollback()


def update_courses(args):
    logging.info('Reading data source %s' % args.datapath)
    with open(args.datapath, 'rt') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)[:args.n] if args.n else list(reader)
        with app.app_context():
            for (i, row) in enumerate(rows):
                logging.info('Processing row %s of %s' % (i + 1, len(rows)))
                prof = models.Professor.query.get(row['DOCENTE_ID'])
                if not prof:
                    prof = models.Professor(
                        id=row['DOCENTE_ID'],
                        first_name=row['NOME'].decode('utf8'),
                        last_name=row['COGNOME'].decode('utf8'),
                        email=row['MAIL'])
                    db.session.add(prof)
                    try:
                        db.session.commit()
                        logging.info('Professor added.')
                    except IntegrityError as e:
                        logging.warn(e.message)
                        db.session.rollback()

                deg = models.Degree.query.filter(
                    models.Degree.code == row['CDS_COD']).first()
                if not deg:
                    deg = models.Degree(
                        code=row['CDS_COD'],
                        name=row['NOME_CDS'].decode('utf8'),
                        category=row['TIPO_CORSO_COD'])
                    db.session.add(deg)
                    try:
                        db.session.commit()
                        logging.info('Degree added.')
                    except IntegrityError as e:
                        logging.warn(e.message)
                        db.session.rollback()

                cur = models.Curriculum.query.filter(
                    and_(models.Curriculum.code == row['PDS_COD'],
                         models.Curriculum.degree_id == deg.id)).first()
                if not cur:
                    cur = models.Curriculum(
                        code=row['PDS_COD'],
                        name=row['PDS_DES'].decode('utf8'),
                        degree=deg)
                    db.session.add(cur)
                    try:
                        db.session.commit()
                        logging.info('Curriculum added.')
                    except IntegrityError as e:
                        logging.warn(e.message)
                        db.session.rollback()

                cal = models.Calendar.query.get(row['AF_ID'])
                if not cal:
                    cal = models.Calendar(id=row['AF_ID'])
                    db.session.add(cal)
                    try:
                        db.session.commit()
                        logging.info('Calendar added.')
                    except IntegrityError as e:
                        logging.warn(e.message)
                        db.session.rollback()

                c = models.Course(
                    id_hash=hashlib.md5(str(row['AF_ID']) +
                                        str(row['AF_ID_MAIN']) +
                                        str(row['AR_ID']) +
                                        str(row['PDS_COD']) +
                                        str(row['DOCENTE_ID'])).hexdigest(),
                    code=row['AF_GEN_COD'],
                    name=row['DES'].decode('utf8'),
                    credit=row['PESO'],
                    total_credit=row['PESO_TOTALE'],
                    period=row['DES_TIPO_CICLO'].decode('utf8'),
                    year=row['ANNO_CORSO'],
                    partition=row['PART_STU_DES'].decode('utf8'),
                    curriculum=cur,
                    calendar=cal,
                    professor=prof)
                db.session.add(c)
                try:
                    db.session.commit()
                    logging.info('Course added.')
                except IntegrityError as e:
                    logging.warn(e.message)
                    db.session.rollback()


def update_calendars(args):
    from datetime import datetime
    date_format = "%d-%m-%Y %H:%M:%S"
    logging.info('Reading data source %s' % args.datapath)
    with open(args.datapath, 'rt') as f:
        data = json.load(f)
        with app.app_context():
            calendars = models.Calendar.query.all()
            for (i, cal) in enumerate(calendars[220:]):
                logging.info('Loading lessons from calendar "%d", %d of %d' %
                             (cal.id, i + 1, len(calendars)))
                events = data[str(cal.id)] if str(cal.id) in data.keys() else None
                if events:
                    for e in events:
                        full_name = e['title'].split(u' - ')[-1].split(u',')[0]
                        professors = models.Professor.query.filter(
                            and_(literal(full_name).contains(models.Professor.first_name),
                                 literal(full_name).contains(models.Professor.last_name))).all()
                        if len(professors) > 1:
                            logging.info('Professors with same name %s' % [p.id for p in professors])
                        if not professors:
                            logging.error('Professor "%s" not found' % full_name)
                            continue

                        loc = models.Location.query.filter(
                            literal(e['description']).contains(
                                models.Location.name)).first()
                        if loc is None:
                            logging.warn(
                                "Can't find location %s" % e['description'])
                        l = models.Lesson(
                            title=e['title'].split(' - ')[0],
                            start=datetime.strptime(e['start'], date_format),
                            end=datetime.strptime(e['end'], date_format),
                            description=e['description'],
                            professor=professors[0],
                            location=loc,
                            calendar=cal)
                        db.session.add(l)
                        try:
                            db.session.commit()
                            logging.info('Lesson added.')
                        except IntegrityError as e:
                            logging.warn(e.message)
                            db.session.rollback()
                else:
                    logging.warning('Calendar %d is empty' % cal.id)


def download_calendars(args):
    from ics import Calendar
    from ics.parse import ParseError

    url = 'http://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid={id}'
    with app.app_context():
        calendars = models.Calendar.query.all()
        data = {}
        try:
            for (i, cal) in enumerate(calendars):
                logging.info('Downloading calendar "%d", %s of %s' % (
                cal.id, i + 1, len(calendars)))
                try:
                    html = urlopen(url.format(id=cal.id)).read().decode(
                        'iso-8859-1')
                    events = Calendar(html).events
                    data[cal.id] = [{'title': e.name,
                                     'start': e.begin.datetime.strftime(
                                         "%d-%m-%Y %H:%M:%S"),
                                     'end': e.end.datetime.strftime(
                                         "%d-%m-%Y %H:%M:%S"),
                                     'description': e.location} for e in
                                    events]
                except HTTPError as e:
                    logging.critical(e.message)
                except ParseError as e:
                    logging.critical(e.message)
        finally:
            logging.info('Storing data')
            with open(args.filename, 'wt') as f:
                json.dump(data, f)


parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(help='commands')

# Update courses command
courses_parser = subparsers.add_parser('courses', help='Update courses')
courses_parser.add_argument('datapath', action='store', help='Data path')
courses_parser.add_argument('-n', action='store',
                            dest='n', type=int, default=None,
                            help='Number of courses')
courses_parser.set_defaults(func=update_courses)

# Update locations command
locations_parser = subparsers.add_parser('locations', help='Update locations')
locations_parser.add_argument('datapath', action='store', help='Data path')
locations_parser.set_defaults(func=update_locations)

# Download calendars command
download_parser = subparsers.add_parser('download', help='Download calendars')
download_parser.add_argument('filename', action='store', help='Output file')
download_parser.set_defaults(func=download_calendars)

# Update calendars command
calendars_parser = subparsers.add_parser('calendars', help='Update calendars')
calendars_parser.add_argument('datapath', action='store', help='Data path')
calendars_parser.set_defaults(func=update_calendars)

args = parser.parse_args()
args.func(args)
