from ics import Calendar, Event
from flask import render_template, redirect, url_for, request, \
    flash, make_response, current_app, g, jsonify
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from .forms import SearchForm
from ..models import Course, Feed
from .. import babel


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


def get_latest_feeds(n=5):
    if not current_user.courses:
        return
    ids = set([c.professor_id for c in current_user.courses])
    feeds = Feed.query.filter(Feed.author_id.in_(ids))
    return feeds.order_by(Feed.timestamp.desc()).limit(n).all()


def count_unread_feeds():
    if not current_user.courses:
        return
    ids = set([c.professor_id for c in current_user.courses])
    return Feed.query.filter(Feed.author_id.in_(ids),
                                 ~Feed.users.contains(current_user)).count()


@main.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated():
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


@main.route('/feed/<int:id>/read/', methods=['post'])
@login_required
def read(id):
    feed = Feed.query.get_or_404(id)
    return jsonify({'success': current_user.read(feed)})


@main.route('/feeds')
@login_required
def feeds():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    ids = set([c.professor_id for c in current_user.courses])
    query = Feed.query.filter(Feed.author_id.in_(ids))
    pagination = query.order_by(Feed.timestamp.desc()).paginate(
        page, per_page=current_app.config['FEEDS_PER_PAGE'],
        error_out=False)
    feeds = pagination.items
    return render_template('feeds.html', form=form, feeds=feeds, pagination=pagination)


@main.route('/download')
@login_required
def download_calendar():
    lessons = [l for c in current_user.courses.all()
               for l in c.lessons.all()]
    cal = Calendar()
    for l in lessons:
        cal.events.append(Event(name=l.title,
                                begin=l.start,
                                end=l.end,
                                location=l.location.address))
    response = make_response(str(cal))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@main.route('/follow', methods=['post'])
@login_required
def follow():
    ids = request.form.getlist('course_id')
    added = 0

    if ids:
        for c in Course.query.filter(Course.id.in_(ids)).all():
            added += current_user.follow(c)

    if added > 0:
        flash('%s new course%s added' %
              (added, 's' if added > 1 else ''), 'info')
    else:
        flash('No new course added', 'danger')

    return redirect(url_for('main.courses'))


@main.route('/unfollow', methods=['post'])
@login_required
def unfollow():
    ids = request.form.getlist('course_id')
    removed = 0

    if ids:
        for c in Course.query.filter(Course.id.in_(ids)).all():
            removed += current_user.unfollow(c)

    if removed > 0:
        flash('%s course%s removed' %
              (removed, 's' if removed > 1 else ''), 'danger')
    else:
        flash('No course removed', 'warning')

    return redirect(url_for('main.courses'))
