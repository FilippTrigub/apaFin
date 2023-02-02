"""Initialize website module"""
# pylint: disable=wrong-import-position
from flask import Flask
from flask.logging import create_logger

app = Flask(__name__)
log = create_logger(app)

import apaFin.web.views
import apaFin.web.stats
