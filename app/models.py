"""
UniveCalendar Database models.
"""
import hashlib

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, \
    URLSafeTimedSerializer

from sqlalchemy import inspect, event, and_
from datetime import datetime
from flask import request, current_app, render_template
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SignallingSession

from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager, bot


follows = db.Table('follows', db.Model.metadata,
                   db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                   db.Column('course_id', db.Integer, db.ForeignKey('courses.id')))

reads = db.Table('reads', db.Model.metadata,
                 db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                 db.Column('feed_id', db.Integer, db.ForeignKey('feeds.id')))

held_at = db.Table('held_at', db.Model.metadata,
                   db.Column('lesson_id', db.Integer, db.ForeignKey('lessons.id')),
                   db.Column('classroom_id', db.Integer, db.ForeignKey('classrooms.id')))

courses_curriculums = db.Table('courses_curriculums', db.Model.metadata,
                               db.Column('course_id', db.Integer, db.ForeignKey('courses.id')),
                               db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculums.id')))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    telegram_chat_id = db.Column(db.String(64))
    courses = db.relationship('Course',
                              secondary=follows,
                              backref='users',
                              lazy='dynamic')
    feeds = db.relationship('Feed',
                            secondary=reads,
                            backref='users')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('Not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def count_credits(self):
        return sum([c.credit for c in self.courses])

    def count_lessons(self):
        return sum([c.calendar.lessons.count() for c in self.courses])

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
            db.session.commit()
            return True
        return False

    def unfollow(self, course):
        if self.is_following(course):
            self.courses.remove(course)
            db.session.commit()
            return True
        return False

    def is_following(self, course):
        return course in self.courses

    def read(self, feed):
        if not self.has_read(feed):
            self.feeds.append(feed)
            db.session.commit()
            return True
        return False

    def unread(self, feed):
        if self.has_read:
            self.feeds.remove(feed)
            db.session.commit()
            return True
        return False

    def has_read(self, feed):
        return feed in self.feeds

    def feeds_query(self):
        if self.courses.count() == 0:
            return
        professor_ids = set([c.professor_id for c in self.courses])
        return Feed.query.filter(Feed.professor_id.in_(professor_ids))

    def count_feeds(self):
        query = self.feeds_query()
        if query is not None:
            return query.count()

    def count_unread_feeds(self):
        query = self.feeds_query()
        if query is not None:
            return query.filter(~Feed.users.contains(self)).count()

    def get_latest_feeds(self, n=3):
        query = self.feeds_query()
        if query is not None:
            return query.order_by(Feed.timestamp.desc()).limit(n).all()

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
        db.session.commit()
        return True

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.commit()
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
        db.session.commit()
        return True

    def generate_unique_code_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'unique_code': self.id})

    @staticmethod
    def load_user_from_unique_code(token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return
        return User.query.get(data.get('unique_code'))

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def to_json(self):
        json_user = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'chat_id': self.telegram_chat_id
        }
        return json_user


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Professor(db.Model):
    __tablename__ = 'professors'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64))
    email = db.Column(db.String(64))
    avatar_url = db.Column(db.String(100))
    avatar_hash = db.Column(db.String(32))
    courses = db.relationship('Course', backref='professor')
    feeds = db.relationship('Feed', backref='professor')

    def __init__(self, **kwargs):
        super(Professor, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None \
                and not self.avatar_url:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    def __repr__(self):
        return '%s %s' % (self.first_name.title(), self.last_name.title())

    @property
    def url(self):
        return 'http://www.unive.it/data/persone/%s' % self.id

    def gravatar(self, size=100, default='identicon', rating='g'):
        if self.avatar_url:
            return self.avatar_url

        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def to_json(self):
        json_user = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'avatar_hash': self.avatar_hash
        }
        return json_user


class Degree(db.Model):
    __tablename__ = 'degrees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, index=True)
    name = db.Column(db.Text, nullable=False)
    category_code = db.Column(db.Enum('LM', 'L', 'D2', 'PAS', 'M1-270', name='categories'))
    category_desc = db.Column(db.Text)
    curriculums = db.relationship('Curriculum', backref='degree')

    def to_json(self):
        json_degree = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category_desc
        }
        return json_degree


class Curriculum(db.Model):
    __tablename__ = 'curriculums'
    __table_args__ = (db.UniqueConstraint('code', 'degree_id'),)
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32))
    name = db.Column(db.Text)
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'))
    courses = db.relationship('Course',
                              secondary=courses_curriculums,
                              backref='curriculums',
                              lazy='dynamic')

    def to_json(self):
        json_curriculum = {
            'id': self.id,
            'degree': self.degree.name,
            'code': self.code,
            'name': self.name
        }
        return json_curriculum


class Course(db.Model):
    __tablename__ = 'courses'
    __sortable__ = ['code', 'name', 'field',
                    'period', 'year', 'partition']
    __table_args__ = (db.UniqueConstraint('id',
                                          'name'),)
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16))
    name = db.Column(db.Text)
    field = db.Column(db.String(16))
    credit = db.Column(db.Integer)
    total_credit = db.Column(db.Integer)
    period = db.Column(db.String(32))
    year = db.Column(db.Integer)
    partition = db.Column(db.String(32))
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendars.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'))

    def __repr__(self):
        return '%s [%s]' % (self.name, self.code.upper())

    @property
    def url(self):
        return 'http://www.unive.it/data/insegnamento/%s' % self.id

    def to_json(self):
        json_course = {
            'id': self.id,
            'code': self.code,
            'url': self.url,
            'name': self.name,
            'degrees': ', '.join(set(c.degree.name for c in self.curriculums)),
            'field': self.field,
            'credit': self.credit,
            'total_credit': self.total_credit,
            'period': self.period,
            'year': self.year,
            'calendar': self.calendar_id,
            'partition': self.partition,
            'professor': str(self.professor)
        }
        return json_course


class Calendar(db.Model):
    __tablename__ = 'calendars'
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship('Course', backref='calendar')
    lessons = db.relationship('Lesson',
                              backref='calendar',
                              lazy='dynamic')

    def lessons_between(self, start, end):
        return self.lessons.filter(and_(Lesson.start >= start, Lesson.end <= end))

    def to_json(self):
        json_calendar = {'id': self.id}
        return json_calendar


class Lesson(db.Model):
    __tablename__ = 'lessons'
    __table_args__ = (db.UniqueConstraint('start',
                                          'end',
                                          'calendar_id',
                                          'description'),)
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime(), nullable=False)
    end = db.Column(db.DateTime(), nullable=False)
    description = db.Column(db.Text)
    has_changed = db.Column(db.Boolean, default=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendars.id'), index=True)
    classrooms = db.relationship('Classroom',
                                 secondary=held_at,
                                 backref='lessons')

    @property
    def duration(self):
        return self.start - self.end

    @property
    def past(self):
        return self.end <= datetime.utcnow()

    def to_json(self, **kwargs):
        json_lesson = {
            'id': self.id,
            'start': self.start.strftime('%Y-%m-%d %H:%M:00'),
            'end': self.end.strftime('%Y-%m-%d %H:%M:00'),
            'past': self.past,
            'has_changed': self.has_changed,
            'description': self.description,
            'classrooms': ', '.join(c.name + ' ' +
                                    c.location.address
                                    for c in self.classrooms)
        }
        for key, value in kwargs.iteritems():
            json_lesson[key] = value
        return json_lesson


def get_old_value(attr_state):
    history = attr_state.load_history()
    return history.deleted[0] if history.deleted else None


def on_lesson_change_event(lesson):
    insp = inspect(lesson)
    start_state = insp.attrs.start
    end_state = insp.attrs.end
    old_start_value = get_old_value(start_state)
    old_end_value = get_old_value(end_state)
    if old_start_value or old_end_value:
        for course in lesson.calendar.courses:
            new_feed = Feed(title='Modifica orario',
                            body=render_template('messages/changed_schedule_feed.txt').format(
                                title=course.name,
                                day=start_state.value.strftime('%d.%m.%Y'),
                                start=start_state.value.strftime('%H:%M %d.%m.%Y'),
                                end=end_state.value.strftime('%H:%M %d.%m.%Y')),
                            professor=course.professor)
            db.session.add(new_feed)
        lesson.has_changed = True


@event.listens_for(SignallingSession, 'before_flush')
def receive_after_flush(session, flush_context, instances):
    for changed_obj in session.dirty:
        if type(changed_obj) is Lesson:
            on_lesson_change_event(changed_obj)


class Classroom(db.Model):
    __tablename__ = 'classrooms'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True)
    name = db.Column(db.Text)
    capacity = db.Column(db.Integer)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    def to_json(self):
        json_classroom = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'capacity': self.capacity,
        }
        if self.location:
            json_classroom.update({
                'address': self.location.address,
                'lat': float(self.location.lat) if self.location.lat else None,
                'lng': float(self.location.lng) if self.location.lng else None,
                'polyline': self.location.polyline
            })
        return json_classroom


class Location(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.UniqueConstraint('name',
                                          'lat',
                                          'lng'),)
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True)
    name = db.Column(db.Text)
    address = db.Column(db.Text)
    lat = db.Column(db.Float(10, 6))
    lng = db.Column(db.Float(10, 6))
    polyline = db.Column(db.Text)
    classrooms = db.relationship('Classroom', backref='location')

    def to_json(self):
        json_location = {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'lat': float(self.lat) if self.lat else None,
            'lng': float(self.lng) if self.lng else None,
            'polyline': self.polyline
        }
        return json_location


class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    professor_id = db.Column(db.Integer,
                             db.ForeignKey('professors.id'),
                             nullable=False)

    def to_json(self):
        json_feed = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'professor': self.professor
        }
        return json_feed


def on_new_feed(mapper, connection, target):
    """Notify users with Telegram message."""
    followers = [u for c in target.professor.courses
                 for u in c.users if u.telegram_chat_id]
    for f in followers:
        bot.send_message(f.telegram_chat_id,
                         '{title}\nFrom: {professor}\n{body}'.format(
                             title=target.title,
                             professor=target.professor,
                             body=target.body))


db.event.listen(Feed, 'after_insert', on_new_feed)
