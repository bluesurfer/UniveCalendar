import os
import logging
import hashlib

from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from openpyxl import load_workbook

from app import models
from manage import app, db
from config import basedir


datapath = os.path.join(basedir, 'data/esploso_corsi_v2.xlsx')

logging.basicConfig(level=logging.INFO)

logging.info('Reading data source')
wb = load_workbook(datapath)
sh = wb.get_active_sheet()
hd = [c.value for c in sh.rows[0]]
rows = sh.rows[1:]

with app.app_context():
    for (i, row) in enumerate(rows):
        logging.info('Processing row %s of %s' % (i, len(rows)))
        prof = models.Professor.query.get(row[hd.index('DOCENTE_ID')].value)
        if not prof:
            prof = models.Professor(
                id=row[hd.index('DOCENTE_ID')].value,
                first_name=row[hd.index('NOME')].value,
                last_name=row[hd.index('COGNOME')].value,
                email=row[hd.index('MAIL')].value)
            db.session.add(prof)
            try:
                db.session.commit()
                logging.info('Professor added.')
            except IntegrityError as e:
                logging.warn(e.message)
                db.session.rollback()

        deg = models.Degree.query.filter(
            models.Degree.code == row[hd.index('CDS_COD')].value).first()
        if not deg:
            deg = models.Degree(
                code=row[hd.index('CDS_COD')].value,
                name=row[hd.index('NOME_CDS')].value,
                category=row[hd.index('TIPO_CORSO_COD')].value)
            db.session.add(deg)
            try:
                db.session.commit()
                logging.info('Degree added.')
            except IntegrityError as e:
                logging.warn(e.message)
                db.session.rollback()

        cur = models.Curriculum.query.filter(
            and_(models.Curriculum.code == row[hd.index('PDS_COD')].value,
                 models.Curriculum.degree_id == deg.id)).first()
        if not cur:
            cur = models.Curriculum(
                code=row[hd.index('PDS_COD')].value,
                name=row[hd.index('PDS_DES')].value,
                degree=deg)
            db.session.add(cur)
            try:
                db.session.commit()
                logging.info('Curriculum added.')
            except IntegrityError as e:
                logging.warn(e.message)
                db.session.rollback()

        cal = models.Calendar.query.get(row[hd.index('AF_ID')].value)
        if not cal:
            cal = models.Calendar(id=row[hd.index('AF_ID')].value)
            db.session.add(cal)
            try:
                db.session.commit()
                logging.info('Calendar added.')
            except IntegrityError as e:
                logging.warn(e.message)
                db.session.rollback()

        c = models.Course(
            id_hash=hashlib.md5(str(row[hd.index('AF_ID')].value) +
                                str(row[hd.index('AF_ID_MAIN')].value) +
                                str(row[hd.index('AR_ID')].value) +
                                str(row[hd.index('PDS_COD')].value) +
                                str(row[hd.index('DOCENTE_ID')].value)).hexdigest(),
            code=row[hd.index('AF_GEN_COD')].value,
            name=row[hd.index('DES')].value,
            credit=row[hd.index('PESO')].value,
            total_credit=row[hd.index('PESO_TOTALE')].value,
            period=row[hd.index('DES_TIPO_CICLO')].value,
            year=row[hd.index('ANNO_CORSO')].value,
            partition=row[hd.index('PART_STU_DES')].value,
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

