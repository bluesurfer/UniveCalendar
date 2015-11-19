from ics import Calendar, Event
from flask import render_template, redirect, url_for, request, \
    flash, make_response, current_app, g
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext, ngettext, lazy_gettext
from flask.ext import breadcrumbs

from . import main
from ..auth import auth
from ..models import Course, Feed
from .. import babel


@main.before_request
@auth.before_request
def add_user_info():
    if current_user.is_authenticated:
        g.total_feeds_count = count_user_feeds()
        g.unread_feeds_count = count_unread_feeds()
        g.latest_feeds = get_latest_feeds(3)
    g.locale = get_locale()


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@babel.localeselector
def get_locale():
    cookie = request.cookies.get("language")
    if cookie in current_app.config['LANGUAGES'].keys():
        return cookie
    return request.accept_languages.best_match(
        current_app.config['LANGUAGES'].keys())


@main.route('/change-language/<lang>')
def change_language(lang):
    response = current_app.make_response(redirect(url_for('main.index')))
    response.set_cookie('language', value=lang)
    return response


def user_feeds_query():
    """Query statement to retrieve user's related feeds."""
    if not current_user.courses:
        return
    professor_ids = set([c.professor_id for c in current_user.courses])
    return Feed.query.filter(Feed.professor_id.in_(professor_ids))


def get_latest_feeds(n=3):
    query = user_feeds_query()
    if query is not None:
        return query.order_by(Feed.timestamp.desc()).limit(n).all()


def count_user_feeds():
    query = user_feeds_query()
    if query is not None:
        return query.count()


def count_unread_feeds():
    query = user_feeds_query()
    if query is not None:
        return query.filter(~Feed.users.contains(current_user)).count()


@main.route('/', methods=['GET', 'POST'])
@breadcrumbs.register_breadcrumb(main, '.', 'Home')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', feeds=get_latest_feeds(5))
    return render_template('welcome.html')


@main.route('/courses')
@login_required
@breadcrumbs.register_breadcrumb(main, '.Courses', lazy_gettext('Courses'))
def courses():
    return render_template('courses.html')


@main.route('/feed/<int:id>')
@login_required
def feed(id):
    f = Feed.query.get_or_404(id)
    current_user.read(f)
    return render_template('view_feed.html', feed=f)


@main.route('/_mark_as_read', methods=['post'])
@login_required
def mark_as_read():
    feed_ids = request.form.getlist('feed_id')
    if feed_ids:
        for f in Feed.query.filter(Feed.id.in_(feed_ids)):
            current_user.read(f)
    return redirect(url_for('main.feeds'))


@main.route('/feeds')
@login_required
def show_feeds():
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
    add_course_info = lambda l, u, t: l.update({'url': u, 'title': t}) or l
    lessons = [add_course_info(l.to_json(), c.url, '%s [%s]' % (c.name, c.code))
               for c in current_user.courses
               for l in c.calendar.lessons]
    calendar = Calendar()
    for l in lessons:
        calendar.events.append(Event(
            name=l['title'],
            begin=l['start'],
            end=l['end'],
            description=l['description']))
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@main.route('/follow', methods=['post'])
@login_required
def follow():
    ids = request.form.getlist('course_id')
    if not ids:
        flash(gettext('No course selected'), 'warning')
        return redirect(url_for('main.courses'))

    added = 0
    courses = Course.query.filter(Course.id.in_(ids))
    for c in courses.all():
        added += current_user.follow(c)

    if added > 0:
        flash(ngettext('%(num)s new course added',
                       '%(num)s new courses added',
                       added), 'info')
    else:
        flash(gettext('No new course added'), 'warning')
    return redirect(url_for('main.courses'))


@main.route('/unfollow', methods=['post'])
@login_required
def unfollow():
    ids = request.form.getlist('course_id')
    if not ids:
        flash(gettext('No course selected'), 'warning')
        return redirect(url_for('main.courses'))

    deleted = 0
    courses = Course.query.filter(Course.id.in_(ids))
    for c in courses.all():
        deleted += current_user.unfollow(c)

    if deleted > 0:
        flash(ngettext('%(num)s course deleted',
                       '%(num)s courses deleted',
                       deleted), 'danger')
    else:
        flash(gettext('No course deleted'), 'info')
    return redirect(url_for('main.courses'))
