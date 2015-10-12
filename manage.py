import os
import sys

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from app import create_app, db, models, bot

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


@bot.message_handler(commands=['start', 'connect'])
def send_welcome(msg):
    token = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    if token:
        with app.app_context():
            u = models.User.load_user_from_unique_code(token)
            if u is not None:
                u.set_chat_id(msg.chat.id)
                reply = "Congratulation {0}, you successfully connect your account.".format(u.username)
            else:
                reply = "I have no clue who you are..."
    else:
        reply = "Please visit me via a provided URL from the website."
    bot.reply_to(msg, reply)


@bot.message_handler(commands=['help'])
def send_welcome(msg):
    reply = "UniveCalendarBot can notify you about events of " \
            "in your university calendar. Visit our page for more info."
    bot.reply_to(msg, reply)


@manager.command
def startbot():
    bot.polling()


@manager.command
def populatedb():
    """Populate database with fake data."""
    models.Location.generate_fake(10)
    models.Professor.generate_fake(50)
    models.Degree.generate_fake(30)
    models.Course.generate_fake(150)
    models.Lesson.generate_fake(1000)


@manager.command
def cleardb():
    """Delete all tables records."""
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@manager.command
def insertfeed(professor_id):
    import forgery_py

    p = models.Professor.query.get(professor_id)
    f = models.Feed(title=forgery_py.lorem_ipsum.title(),
                    body=forgery_py.lorem_ipsum.paragraphs(2),
                    professor=p)

    db.session.add(f)
    db.session.commit()


@manager.command
def delaylesson(lesson_id, hours=1):
    from datetime import timedelta

    l = models.Lesson.query.get(lesson_id)
    l.start += timedelta(hours=hours)
    l.end += timedelta(hours=hours)
    db.session.commit()


@manager.command
def adduser():
    u = models.User(email='bob@unive.it',
                    username='bobby85',
                    confirmed=True,
                    password='123456')
    db.session.add(u)
    db.session.commit()


@manager.command
def deleteusers():
    models.User.query.delete()
    db.session.commit()


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware

    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                      restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def trcompile():
    if sys.platform == 'win32':
        pybabel = 'flask\\Scripts\\pybabel'
    else:
        pybabel = 'pybabel'
    os.system(pybabel + ' compile -d app/translations')


@manager.command
def trupdate():
    if sys.platform == 'win32':
        pybabel = 'flask\\Scripts\\pybabel'
    else:
        pybabel = 'pybabel'
    os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot app')
    os.system(pybabel + ' update -i messages.pot -d app/translations')
    os.unlink('messages.pot')


@manager.command
def trinit():
    if sys.platform == 'win32':
        pybabel = 'flask\\Scripts\\pybabel'
    else:
        pybabel = 'pybabel'
    if len(sys.argv) != 2:
        print "usage: tr_init <language-code>"
        sys.exit(1)
    os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot app')
    os.system(pybabel + ' init -i messages.pot -d app/translations -l ' + sys.argv[1])
    os.unlink('messages.pot')


if __name__ == '__main__':
    manager.run()
