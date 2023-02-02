import unittest
import yaml
import re
import requests_mock
from apaFin.hunter import Hunter
from apaFin.idmaintainer import IdMaintainer
from dummy_crawler import DummyCrawler
from test_util import count
from utils.config import StringConfig

class GMapsDurationProcessorTest(unittest.TestCase):

    DUMMY_CONFIG = """
urls:
  - https://www.example.com/liste/berlin/wohnungen/mieten?roomi=2&prima=1500&wflmi=70&sort=createdate%2Bdesc

google_maps_api:
  key: SOME_KEY
  url: https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={dest}&mode={mode}&sensor=true&key={key}&arrival_time={arrival}
  enable: true

durations:
  - destination: Buckingham Palace UK
    name: The Queen
    modes:
      - gm_id: transit
        title: By Bus
  - destination: главная площадь
    name: Москва
    modes:
      - gm_id: bicycling
        title: Bicyle
      - gm_id: driving
        title: Car
    """

    @requests_mock.Mocker()
    def test_resolve_durations(self, m):
        config = StringConfig(string=self.DUMMY_CONFIG)
        config.set_searchers([DummyCrawler()])
        hunter = Hunter(config, IdMaintainer(":memory:"))
        matcher = re.compile('maps.googleapis.com/maps/api/distancematrix/json')
        m.get(matcher, text='{"status": "OK", "rows": [ { "elements": [ { "distance": { "text": "far", "value": 123 }, "duration": { "text": "days", "value": 123 } } ] } ]}')
        exposes = hunter.hunt_flats()
        self.assertTrue(count(exposes) > 4, "Expected to find exposes")
        without_durations = list(filter(lambda expose: 'durations' not in expose, exposes))
        if len(without_durations) > 0:
            for expose in without_durations:
                print("Got expose: ", expose)
        self.assertTrue(len(without_durations) == 0, "Expected durations to be calculated")