import pytest
import tempfile
import yaml
import json
import requests_mock

from flask import session

from apaFin.web import app
from apaFin.web_hunter import WebHunter
from apaFin.idmaintainer import IdMaintainer

from dummy_crawler import DummyCrawler
from utils.config import StringConfig

DUMMY_CONFIG = """
notifiers:
  - telegram

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

def test_get_index(hunt_client):
    rv = hunt_client.get('/')
    assert b'<a class="navbar-brand" href="/">ApaFin</a>' in rv.data

def test_get_about(hunt_client):
    rv = hunt_client.get('/about')
    assert b'<a class="navbar-brand" href="/">ApaFin</a>' in rv.data

def test_get_resources(hunt_client):
    rv = hunt_client.get('/resources')
    assert b'<a class="navbar-brand" href="/">ApaFin</a>' in rv.data

def test_get_index_with_exposes(hunt_client):
    app.config['HUNTER'].hunt_flats()
    rv = hunt_client.get('/')
    assert b'<div class="expose' in rv.data

@requests_mock.Mocker(kw='m')
def test_hunt_with_users(hunt_client, **kwargs):
    m = kwargs['m']
    mock_response = '{"ok":true,"result":{"message_id":456,"from":{"id":1,"is_bot":true,"first_name":"Wohnbot","username":"wohnung_search_bot"},"chat":{"id":5,"first_name":"Arthur","last_name":"Taylor","type":"private"},"date":1589813130,"text":"hello arthur"}}'
    for title in [ 'wg', 'ruhig', 'gruen', 'tausch', 'flat' ]:
        m.post('https://api.telegram.org/bot1234xxx.12345/sendMessage', text=mock_response)
    app.config['HUNTER'].set_filters_for_user(1234, {})
    assert app.config['HUNTER'].get_filters_for_user(1234) == {}
    app.config['HUNTER'].hunt_flats()
    assert len(m.request_history) == 24
    rv = hunt_client.get('/')
    assert b'<div class="expose' in rv.data

@requests_mock.Mocker(kw='m')
def test_hunt_via_post(hunt_client, **kwargs):
    m = kwargs['m']
    mock_response = '{"ok":true,"result":{"message_id":456,"from":{"id":1,"is_bot":true,"first_name":"Wohnbot","username":"wohnung_search_bot"},"chat":{"id":5,"first_name":"Arthur","last_name":"Taylor","type":"private"},"date":1589813130,"text":"hello arthur"}}'
    for title in [ 'wg', 'ruhig', 'gruen', 'tausch', 'flat' ]:
        m.post('https://api.telegram.org/bot1234xxx.12345/sendMessage', text=mock_response)
    app.config['HUNTER'].set_filters_for_user(1234, {})
    assert app.config['HUNTER'].get_filters_for_user(1234) == {}
    rv = hunt_client.get('/hunt')
    assert len(m.request_history) == 24
    assert '<div class="expose' in json.loads(rv.data)['body']

@requests_mock.Mocker(kw='m')
def test_multi_user_hunt_via_post(hunt_client, **kwargs):
    m = kwargs['m']
    mock_response = '{"ok":true,"result":{"message_id":456,"from":{"id":1,"is_bot":true,"first_name":"Wohnbot","username":"wohnung_search_bot"},"chat":{"id":5,"first_name":"Arthur","last_name":"Taylor","type":"private"},"date":1589813130,"text":"hello arthur"}}'
    for title in [ 'wg', 'ruhig', 'gruen', 'tausch', 'flat' ]:
        m.post('https://api.telegram.org/bot1234xxx.12345/sendMessage', text=mock_response)
    app.config['HUNTER'].set_filters_for_user(1234, {})
    app.config['HUNTER'].set_filters_for_user(1235, {})
    assert app.config['HUNTER'].get_filters_for_user(1234) == {}
    rv = hunt_client.get('/hunt')
    assert len(m.request_history) == 48
    assert '<div class="expose' in json.loads(rv.data)['body']

@requests_mock.Mocker(kw='m')
def test_hunt_via_post_with_filters(hunt_client, **kwargs):
    m = kwargs['m']
    mock_response = '{"ok":true,"result":{"message_id":456,"from":{"id":1,"is_bot":true,"first_name":"Wohnbot","username":"wohnung_search_bot"},"chat":{"id":5,"first_name":"Arthur","last_name":"Taylor","type":"private"},"date":1589813130,"text":"hello arthur"}}'
    for title in [ 'wg', 'gruen', 'flat' ]:
        m.post('https://api.telegram.org/bot1234xxx.12345/sendMessage', text=mock_response)
    app.config['HUNTER'].set_filters_for_user(1234, { 'excluded_titles': [ 'ruhig', 'tausch' ] })
    assert app.config['HUNTER'].get_filters_for_user(1234) == { 'excluded_titles': [ 'ruhig', 'tausch' ]}
    rv = hunt_client.get('/hunt')
    assert len(m.request_history) == 15
    assert '<div class="expose' in json.loads(rv.data)['body']

def test_render_index_after_login(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    rv = hunt_client.get('/')
    assert rv.status_code == 200
 
@requests_mock.Mocker(kw='m')
def test_do_not_send_messages_if_notifications_disabled(hunt_client, **kwargs):
    m = kwargs['m']
    app.config['HUNTER'].set_filters_for_user(1234, {})
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    rv = hunt_client.post('/toggle_notifications')
    assert rv.status_code == 201
    rv = hunt_client.get('/hunt')
    assert '<div class="expose' in json.loads(rv.data)['body']

def test_toggle_notification_status_when_logged_out_fails(hunt_client):
    rv = hunt_client.post('/toggle_notifications')
    assert rv.status_code == 404

def test_toggle_notification_status(hunt_client):
    app.config['HUNTER'].set_filters_for_user(1234, {})
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    rv = hunt_client.post('/toggle_notifications')
    assert rv.status_code == 201
    assert not json.loads(rv.data)['notifications_enabled']
    rv = hunt_client.post('/toggle_notifications')
    assert rv.status_code == 201
    assert json.loads(rv.data)['notifications_enabled']

def test_update_filters(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    rv = hunt_client.post('/filter', data = { 'b': '3' })
    assert app.config['HUNTER'].get_filters_for_user(1234) == { 'b': 3.0 }

def test_update_filters_not_logged_in(hunt_client):
    rv = hunt_client.post('/filter', data = { 'b': '3' })
    assert 'user' not in session
    assert app.config['HUNTER'].get_filters_for_user(1234) is None

def test_index_logged_in_with_filters(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    hunt_client.post('/filter', data = { 'max_size': '35' })
    rv = hunt_client.get('/')
    assert b'<input type="text" class="form-control" id="max_size" name="max_size" placeholder="any" value="35">' in rv.data

def test_login_with_telegram(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    assert session['user']['first_name'] == 'Jason'
    assert json.dumps(session['user']) == '{"id": "1234", "first_name": "Jason", "last_name": "Bourne", "username": "mattdamon", "photo_url": "https://i.example.com/profile.jpg", "auth_date": "123455678"}'

def test_login_with_invalid_url(hunt_client):
    rv = hunt_client.get('/login_with_telegram?username=mattdamon&id=1234&first_name=Jason&last_name=Bourne&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' not in session

def test_login_with_missing_params(hunt_client):
    rv = hunt_client.get('/login_with_telegram?ad=1234&hash=51d737e1a3ba0821359955a36d3671f2957b5a8f1f32f9a133ce95836c44a9a9')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' not in session

def test_login_with_invalid_hash(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=0091a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25900')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' not in session

def test_logout(hunt_client):
    rv = hunt_client.get('/login_with_telegram?id=1234&first_name=Jason&last_name=Bourne&username=mattdamon&photo_url=https%3A%2F%2Fi.example.com%2Fprofile.jpg&auth_date=123455678&hash=c691a55de4e28b341ccd0b793d4ca17f09f6c87b28f8a893621df81475c25952')
    assert rv.status_code == 302
    assert rv.headers['location'] == '/'
    assert 'user' in session
    rv = hunt_client.get('/logout')
    assert 'user' not in session
