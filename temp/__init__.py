"""Mossie package initialization."""

import flask
import os

app = flask.Flask(__name__)

app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_only_for_development'),
    DATABASE_FILENAME=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp', 'mossie.db')
)

# Import routes after app is created to avoid circular imports
import temp.views

# Import and register extended features
from temp.features import features
app.register_blueprint(features)

# Import database models
from . import models
models.init_app(app)
