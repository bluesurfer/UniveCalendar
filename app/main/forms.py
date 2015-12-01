from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired, Length
from flask.ext.babel import lazy_gettext


class SearchFeedForm(Form):
    search = StringField(lazy_gettext('Search feed'), validators=[
        DataRequired(),
        Length(1, 64)])
