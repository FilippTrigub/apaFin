import pytest
import tempfile
import yaml
import json
import requests_mock

from flask import session

from flathunter.web import app
from flathunter.web_hunter import WebHunter
from flathunter.idmaintainer import IdMaintainer

from dummy_crawler import DummyCrawler
from utils.config import StringConfig

DUMMY_CONFIG = """
telegram:
  bot_token: 1234xxx.12345

message: "{title}"

urls:
  - https://www.example.com/liste/berlin/wohnungen/mieten?roomi=2&prima=1500&wflmi=70&sort=createdate%2Bdesc
    """

@pytest.fixture
def hunt_client():
    app.config['TESTING'] = True
    with tempfile.NamedTemporaryFile(mode='w+') as temp_db:
        config = StringConfig(string=DUMMY_CONFIG)
        config.set_searchers([DummyCrawler()])
        app.config['HUNTER'] = WebHunter(config, IdMaintainer(temp_db.name))
        app.config['BOT_TOKEN'] = "1234xxx.12345"
        app.secret_key = b'test_session_key'

        with app.test_client() as hunt_client:
            yield hunt_client

def test_statistics_view(hunt_client):
    rv = hunt_client.get('/stats')
    assert b'<a class="navbar-brand" href="/">Flathunter</a>' in rv.data
