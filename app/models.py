# coding=utf-8
import hashlib

from sqlalchemy import event, inspect
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from datetime import datetime, timedelta
from flask import request, current_app
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SignallingSession

from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


# A base64 image of a happy robot
ROBOT_AVATAR = "data:image/png;base64,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"

# System messages
CHANGED_SCHEDULE = u"L'orario della lezione '{title}' è stato modificato: la lezione si terrà il giorno {day} dalle {start} alle {end}"

follows = db.Table('follows', db.Model.metadata,
                   db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                   db.Column('course_id', db.Integer, db.ForeignKey('courses.id')))

reads = db.Table('reads', db.Model.metadata,
                 db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                 db.Column('feed_id', db.Integer, db.ForeignKey('feeds.id')))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    username = db.Column(db.String(64), unique=True)
    phone_number = db.Column(db.String(32))
    notify_me = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    courses = db.relationship('Course',
                              backref='user_id',
                              secondary=follows,
                              lazy='dynamic')
    feeds = db.relationship('Feed',
                            backref='user_id',
                            secondary=reads,
                            lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('Not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def follow(self, course):
        if not self.is_following(course):
            self.courses.append(course)
            db.session.add(course)
            db.session.commit()
            return True
        return False

    def unfollow(self, course):
        c = self.courses.filter_by(id=course.id).first()
        if c:
            self.courses.remove(c)
            db.session.commit()
            return True
        return False

    def is_following(self, course):
        return self.courses.filter_by(id=course.id).first() is not None

    def read(self, feed):
        if not self.has_read(feed):
            self.feeds.append(feed)
            db.session.add(feed)
            db.session.commit()
            return True
        return False

    def unread(self, feed):
        f = self.feeds.filter_by(id=feed.id).first()
        if f:
            self.feeds.remove(f)
            db.session.commit()
            return True
        return False

    def has_read(self, feed):
        return self.feeds.filter_by(id=feed.id).first() is not None

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def to_json(self):
        json_user = {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
        return json_user


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Professor(db.Model):
    __tablename__ = 'professors'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    avatar_hash = db.Column(db.String(32))
    courses = db.relationship('Course',
                              backref='professor',
                              lazy='dynamic')
    feeds = db.relationship('Feed',
                            backref='professor',
                            lazy='dynamic')

    def __init__(self, **kwargs):
        super(Professor, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def on_append_feed(target, value, initiator):
        print 'new feed'

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()

        for i in range(count):
            p = Professor(first_name=forgery_py.name.first_name(),
                          last_name=forgery_py.name.last_name(),
                          email=forgery_py.internet.email_address())
            db.session.add(p)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        json_user = {
            'id': self.id,
            'first_name': self.first_name,
            'last_naem': self.last_name,
            'email': self.email,
            'avatar_hash': self.avatar_hash
        }
        return json_user


db.event.listen(Professor.feeds, 'append', Professor.on_append_feed)


class Degree(db.Model):
    __tablename__ = 'degrees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(64))
    category = db.Column(db.Enum('bachelor', 'master', name='categories'))
    courses = db.relationship('Course',
                              backref='degree',
                              lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, choice
        import forgery_py

        seed()

        for i in range(count):
            d = Degree(code=forgery_py.basic.text(3),
                       name=forgery_py.lorem_ipsum.title(),
                       category=choice([0, 1]))
            db.session.add(d)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        json_degree = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category
        }
        return json_degree


class Course(db.Model):
    __tablename__ = 'courses'
    __table_args__ = (db.UniqueConstraint('id',
                                          'code',
                                          'name',
                                          'professor_id',
                                          'partition'),)
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16))
    url = db.Column(db.String(64))
    name = db.Column(db.String(64))
    academic_year = db.Column(db.String(32))
    field = db.Column(db.String(16))
    credit = db.Column(db.Integer)
    period = db.Column(db.String(32))
    year = db.Column(db.Integer)
    partition = db.Column(db.String(32))
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'))
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'))
    lessons = db.relationship('Lesson',
                              backref='course',
                              lazy='joined')
    users = db.relationship('User',
                            secondary=follows,
                            backref=db.backref('course_id', lazy='dynamic'),
                            lazy='dynamic')

    def to_json(self):
        prof_full_name = self.professor.first_name + ' ' + self.professor.last_name
        json_degree = {
            'id': self.id,
            'code': self.code,
            'url': self.url,
            'name': self.name,
            'academic_year': self.academic_year,
            'field': self.field,
            'credit': self.credit,
            'period': self.period,
            'year': self.year,
            'partition': self.partition,
            'professor': prof_full_name
        }
        return json_degree

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()

        professor_count = Professor.query.count()
        degree_count = Degree.query.count()

        for i in range(count):
            d = Degree.query.offset(randint(0, degree_count - 1)).first()
            p = Professor.query.offset(randint(0, professor_count - 1)).first()
            c = Course(code=forgery_py.basic.text(5).upper(),
                       url=forgery_py.internet.domain_name(),
                       name=forgery_py.lorem_ipsum.title(),
                       academic_year='2015/2016',
                       field=forgery_py.basic.text(5).upper(),
                       credit=randint(0, 12),
                       period='1',
                       year=randint(1, 3),
                       partition='',
                       degree=d,
                       professor=p)
            db.session.add(c)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())
    url = db.Column(db.String(64))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    feeds = db.relationship('Feed',
                            backref='lesson',
                            lazy='dynamic')

    def to_json(self):
        json_lesson = {
            'id': self.id,
            'title': self.title,
            'start': self.start,
            'url': self.course.url,
            'end': self.end
        }
        return json_lesson

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()

        course_count = Course.query.count()
        location_count = Location.query.count()
        for i in range(count):
            c = Course.query.offset(randint(0, course_count - 1)).first()
            loc = Location.query.offset(randint(0, location_count - 1)).first()
            start = datetime.combine(forgery_py.date.date(), datetime.min.time())
            start += timedelta(hours=randint(8, 15))
            l = Lesson(title=forgery_py.lorem_ipsum.title(),
                       start=start,
                       end=start + timedelta(hours=randint(1, 4)),
                       url=forgery_py.internet.domain_name(),
                       course=c,
                       location=loc)

            db.session.add(l)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


def get_old_value(attr_state):
    history = attr_state.load_history()
    return history.deleted[0] if history.deleted else None


def add_lesson_feed(title, body, lesson):
    feed = Feed(title=title, body=body, lesson=lesson)
    lesson.feeds.append(feed)
    db.session.add(feed)


def trigger_lesson_change_events(lesson):
    insp = inspect(lesson)
    start_state = insp.attrs.start
    end_state = insp.attrs.end
    old_start_value = get_old_value(start_state)
    old_end_value = get_old_value(end_state)
    # Does the lesson schedule change?
    if old_start_value or old_end_value:
        add_lesson_feed(title='Modifica orario',
                        body=CHANGED_SCHEDULE.format(
                            title=lesson.title,
                            day=start_state.value.strftime('%d.%m.%Y'),
                            start=start_state.value.strftime('%H:%M'),
                            end=end_state.value.strftime('%H:%M')),
                        lesson=lesson)


@event.listens_for(SignallingSession, 'after_flush')
def receive_after_flush(session, flush_context):
    for changed_obj in session.dirty:
        if type(changed_obj) is Lesson:
            trigger_lesson_change_events(changed_obj)


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(64))
    address = db.Column(db.String(64))
    coordinates = db.Column(db.String(64))
    lessons = db.relationship('Lesson',
                              backref='location',
                              lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()

        for i in range(count):
            l = Location(city=forgery_py.address.city(),
                         address=forgery_py.address.street_address(),
                         coordinates='')
            db.session.add(l)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    users = db.relationship('User',
                            secondary=reads,
                            backref=db.backref('feed_id', lazy='dynamic'),
                            lazy='dynamic')

    @property
    def author(self):
        if self.professor:
            return self.professor.first_name + ' ' + self.professor.last_name
        return 'System Alert'

    @property
    def contact(self):
        if self.professor:
            return self.professor.email
        return 'codeforveniceteam@gmail.com'

    @property
    def gravatar(self):
        if self.professor:
            return self.professor.gravatar()
        return ROBOT_AVATAR

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()

        professor_count = Professor.query.count()
        for i in range(count):
            p = Professor.query.offset(randint(0, professor_count - 1)).first()
            timestamp = datetime.combine(forgery_py.date.date(past=True), datetime.min.time())
            timestamp += timedelta(hours=randint(0, 24), minutes=randint(0, 59))
            f = Feed(title=forgery_py.lorem_ipsum.title(),
                     body=forgery_py.lorem_ipsum.paragraphs(2),
                     timestamp=timestamp,
                     professor=p)
            db.session.add(f)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def to_json(self):
        json_feed = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'author': self.author
        }
        return json_feed
