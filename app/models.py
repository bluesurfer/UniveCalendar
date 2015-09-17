import hashlib

from datetime import datetime, timedelta
from flask import request
from flask.ext.login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


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
    password_hash = db.Column(db.String(128))
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

    def follow(self, course):
        if not self.is_following(course):
            self.courses.append(course)
            db.session.add(course)
            return True
        return False

    def unfollow(self, course):
        c = self.courses.filter_by(id=course.id).first()
        if c:
            self.courses.remove(c)
            return True
        return False

    def is_following(self, course):
        return self.courses.filter_by(id=course.id).first() is not None

    def read(self, feed):
        if not self.has_read(feed):
            self.feeds.append(feed)
            db.session.add(feed)
            return True
        return False

    def unread(self, feed):
        f = self.feeds.filter_by(id=feed.id).first()
        if f:
            self.feeds.remove(f)
            return True
        return False

    def has_read(self, feed):
        return self.feeds.filter_by(id=feed.id).first() is not None

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
                            backref='author',
                            lazy='joined')

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


class Degree(db.Model):
    __tablename__ = 'degrees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(64))
    category = db.Column(db.String(64))
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
                       category=choice(['triennale', 'magistrale']))
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
                              lazy='dynamic')
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
                       field=forgery_py.name.suffix(),
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
    author_id = db.Column(db.Integer, db.ForeignKey('professors.id'))
    users = db.relationship('User',
                            secondary=reads,
                            backref=db.backref('feed_id', lazy='dynamic'),
                            lazy='dynamic')

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
                     author=p)
            db.session.add(f)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def to_json(self):
        full_name = self.author.first_name + ' ' + self.author.last_name
        json_feed = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'author': full_name
        }
        return json_feed

