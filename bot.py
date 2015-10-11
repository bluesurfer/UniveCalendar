import os
import telebot

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, event

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from config import config


config = config[os.getenv('FLASK_CONFIG') or 'development']

# Initialize database connection.
Base = automap_base()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, connect_args={'check_same_thread':False})
Base.prepare(engine, reflect=True)
User = Base.classes.users
Feed = Base.classes.feeds
session = Session(engine)

# Initialize Telegram bot
bot = telebot.TeleBot(config.BOT_TOKEN)

u = session.query(User).get(1)


@event.listens_for(Feed, 'after_insert')
def on_new_feed(mapper, connection, target):
    users = [u for c in target.courses for u in c.users]
    for u in users:
        if u.telegram_chat_id:
            bot.send_message(u.telegram_chat_id)
    print "received append event for target: %s" % target


def load_user(token):
    s = Serializer(config.SECRET_KEY)
    try:
        data = s.loads(token)
    except:
        return
    return session.query(User).get(data.get('unique_code'))


def extract_token(text):
    # Extracts the unique_code from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


def foo():
    u = User.query.get(1)
    print u.generate_unique_code_token()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    token = extract_token(message.text)
    if token:
        u = load_user(token)
        if u is not None:
            u.telegram_chat_id = message.chat.id
            session.commit()
            reply = "Hello {0}, how are you?".format(u.username)
        else:
            reply = "I have no clue who you are..."
    else:
        reply = "Please visit me via a provided URL from the website."
    bot.reply_to(message, reply)


bot.polling()