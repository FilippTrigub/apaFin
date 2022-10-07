import pytest
import datetime
import re
from mockfirestore import MockFirestore

from flathunter.googlecloud_idmaintainer import GoogleCloudIdMaintainer
from flathunter.hunter import Hunter
from flathunter.web_hunter import WebHunter
from flathunter.filter import Filter
from dummy_crawler import DummyCrawler
from test_util import count
from utils.config import StringConfig

class MockGoogleCloudIdMaintainer(GoogleCloudIdMaintainer):

    def __init__(self):
        self.database = MockFirestore()

CONFIG_WITH_FILTERS = """
urls:
  - https://www.example.com/liste/berlin/wohnungen/mieten?roomi=2&prima=1500&wflmi=70&sort=createdate%2Bdesc

filters:
  max_price: 1000
    """

@pytest.fixture
def id_watch():
    return MockGoogleCloudIdMaintainer()
    
def test_read_after_write(id_watch):
    id_watch.mark_processed(12345)
    assert id_watch.is_processed(12345)

def test_get_last_run_time_none_by_default(id_watch):
    assert id_watch.get_last_run_time() == None

def test_get_list_run_time_is_updated(id_watch):
    time = id_watch.update_last_run_time()
    assert time != None
    assert time == id_watch.get_last_run_time()

def test_is_processed_works(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    config.set_searchers([DummyCrawler()])
    hunter = Hunter(config, id_watch)
    exposes = hunter.hunt_flats()
    assert count(exposes) > 4
    for expose in exposes:
        assert id_watch.is_processed(expose['id'])

def test_exposes_are_saved_to_maintainer(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    config.set_searchers([DummyCrawler()])
    hunter = Hunter(config, id_watch)
    exposes = hunter.hunt_flats()
    assert count(exposes) > 4
    saved = id_watch.get_exposes_since(datetime.datetime.now() - datetime.timedelta(seconds=10))
    assert len(saved) > 0
    assert count(exposes) < len(saved)

def test_exposes_are_returned_as_dictionaries(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    config.set_searchers([DummyCrawler()])
    hunter = Hunter(config, id_watch)
    hunter.hunt_flats()
    saved = id_watch.get_exposes_since(datetime.datetime.now() - datetime.timedelta(seconds=10))
    assert len(saved) > 0
    expose = saved[0]
    assert expose['title'] is not None
    assert expose['created_at'] is not None

def test_exposes_are_returned_with_limit(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    config.set_searchers([DummyCrawler()])
    hunter = Hunter(config, id_watch)
    hunter.hunt_flats()
    saved = id_watch.get_recent_exposes(10)
    assert len(saved) == 10
    expose = saved[0]
    assert expose['title'] is not None

def test_exposes_are_returned_filtered(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    config.set_searchers([DummyCrawler()])
    hunter = Hunter(config, id_watch)
    hunter.hunt_flats()
    hunter.hunt_flats()
    filter = Filter.builder().max_size_filter(70).build()
    saved = id_watch.get_recent_exposes(10, filter_set=filter)
    assert len(saved) == 10
    for expose in saved:
        assert int(re.match(r'\d+', expose['size'])[0]) <= 70

def test_filters_for_user_are_saved(id_watch):
    filter = { 'fish': 'cat' }
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    hunter = WebHunter(config, id_watch)
    hunter.set_filters_for_user(123, filter)
    assert hunter.get_filters_for_user(123) == filter

def test_filters_for_user_returns_none_if_none_present(id_watch):
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    hunter = WebHunter(config, id_watch)
    assert hunter.get_filters_for_user(123) == None
    assert hunter.get_filters_for_user(None) == None

def test_all_filters_can_be_loaded(id_watch):
    filter = { 'fish': 'cat' }
    config = StringConfig(string=CONFIG_WITH_FILTERS)
    hunter = WebHunter(config, id_watch)
    hunter.set_filters_for_user(123, filter)
    hunter.set_filters_for_user(124, filter)
    assert id_watch.get_user_settings() == [ (123, { 'filters': filter }), (124, { 'filters': filter }) ]
