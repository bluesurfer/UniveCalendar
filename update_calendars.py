import logging
import ics

from sqlalchemy.exc import IntegrityError
from urllib2 import urlopen, HTTPError

from app import models
from manage import app, db

logging.basicConfig(level=logging.INFO)

url = 'http://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid={id}'

with app.app_context():
    calendars = models.Calendar.query.all()
    for (i, cal) in enumerate(calendars):
        logging.info('Downloading calendar "%d", %s of %s' % (cal.id, i + 1, len(calendars)))
        try:
            html = urlopen(url.format(id=cal.id)).read().decode('iso-8859-1')
            events = ics.Calendar(html).events
            if events:
                for e in events:
                    l = models.Lesson(
                        title=e.name,
                        start=e.begin.datetime,
                        end=e.end.datetime,
                        location=e.location,
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
        except HTTPError as e:
            logging.critical(e.message)