from sqlalchemy import or_
from ics import Calendar, Event
from flask import render_template, redirect, url_for, request, \
    flash, make_response, current_app, g, jsonify
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext, ngettext
from . import main
from forms import EditProfileForm
from ..models import Course, Feed
from .. import babel
from ..email import send_email


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(
        current_app.config['LANGUAGES'].keys())


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.before_request
@login_required
def before_request():
    g.unread = count_unread_feeds()
    g.latest = get_latest_feeds(3)
    g.locale = get_locale()


def user_feeds_query():
    """The SQL query that retrieves user's related feeds."""
    if not current_user.courses.count():
        return
    professor_ids = set([c.professor_id for c in current_user.courses])
    lesson_ids = [l.id for c in current_user.courses for l in c.lessons]
    return Feed.query.filter(or_(Feed.professor_id.in_(professor_ids),
                                 Feed.lesson_id.in_(lesson_ids)))


def get_latest_feeds(n=5):
    query = user_feeds_query()
    if query is not None:
        return query.order_by(Feed.timestamp.desc()).limit(n).all()


def count_unread_feeds():
    query = user_feeds_query()
    if query is not None:
        return query.filter(~Feed.users.contains(current_user)).count()


@main.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return render_template('index.html', feeds=get_latest_feeds(5))
    return redirect(url_for('auth.login'))


@main.route('/courses')
@login_required
def courses():
    return render_template('courses.html')


@main.route('/feed/<int:id>')
@login_required
def feed(id):
    feed = Feed.query.get_or_404(id)
    current_user.read(feed)
    return render_template('feed.html', feed=feed)


@main.route('/_mark_as_read', methods=['post'])
@login_required
def mark_as_read():
    feed_ids = request.form.getlist('feed_id')
    if feed_ids:
        feeds = Feed.query.filter(Feed.id.in_(feed_ids))
        for f in feeds:
            current_user.read(f)
    return redirect(url_for('main.feeds'))


@main.route('/feeds')
@login_required
def feeds():
    page = request.args.get('page', 1, type=int)
    query = user_feeds_query()
    if not query:
        return render_template('feeds.html')
    pagination = query.order_by(Feed.timestamp.desc()).paginate(
        page, per_page=current_app.config['FEEDS_PER_PAGE'],
        error_out=False)
    feeds = pagination.items
    return render_template('feeds.html', feeds=feeds, pagination=pagination)


@main.route('/download')
@login_required
def download_calendar():
    lessons = [l for c in current_user.courses for l in c.lessons]
    calendar = Calendar()
    for l in lessons:
        calendar.events.append(Event(name=l.title,
                                     begin=l.start,
                                     end=l.end,
                                     location=l.location.address))
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@main.route('/follow', methods=['post'])
@login_required
def follow():
    course_ids = request.form.getlist('course_id')
    if not course_ids:
        flash(gettext('No course selected'), 'warning')
        return redirect(url_for('main.courses'))

    added = 0
    for c in Course.query.filter(Course.id.in_(course_ids)).all():
        added += current_user.follow(c)

    if added > 0:
        flash(ngettext('%(num)s new course added',
                       '%(num)s new courses added', added), 'info')
    else:
        flash(gettext('No new course added'), 'warning')

    return redirect(url_for('main.courses'))


@main.route('/unfollow', methods=['post'])
@login_required
def unfollow():
    course_ids = request.form.getlist('course_id')
    if not course_ids:
        flash(gettext('No course selected'), 'warning')
        return redirect(url_for('main.courses'))

    deleted = 0
    for c in Course.query.filter(Course.id.in_(course_ids)).all():
        deleted += current_user.unfollow(c)

    if deleted > 0:
        flash(ngettext('%(num)s course deleted',
                       '%(num)s courses deleted', deleted), 'danger')
    else:
        flash(gettext('No course deleted'), 'info')

    return redirect(url_for('main.courses'))

