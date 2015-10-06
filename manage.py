import os

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from app import create_app, db, models

app = create_app(os.getenv('FLASK_CONFIG') or 'production')
migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


@manager.command
def populatedb():
    """Populate database with fake data."""
    models.Location.generate_fake(10)
    models.Professor.generate_fake(50)
    models.Degree.generate_fake(30)
    models.Course.generate_fake(150)
    models.Lesson.generate_fake(1000)


@manager.command
def insertfeed(professor_id):
    import datetime
    import forgery_py

    p = models.Professor.query.get(professor_id)
    f = models.Feed(title=forgery_py.lorem_ipsum.title(),
                    body=forgery_py.lorem_ipsum.paragraphs(2),
                    timestamp=datetime.datetime.now(),
                    professor=p)

    db.session.add(f)
    db.session.commit()


@manager.command
def addusers():
    u = models.User(email='bob@unive.it',
                    username='bob',
                    confirmed=True,
                    password='123456')

    db.session.add(u)
    db.session.commit()

    u = models.User(email='alice@unive.it',
                    username='alice',
                    password='123456')

    db.session.add(u)
    db.session.commit()


@manager.command
def deleteusers():
    models.User.query.delete()
    db.session.commit()


@manager.command
def cleardb():
    """Delete all tables records."""
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware

    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                      restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


if __name__ == '__main__':
    manager.run()
