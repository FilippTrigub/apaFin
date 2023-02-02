import json
import unittest

from requests_mock import Mocker
from utils.request_matcher import RequestCounter
from utils.config import StringConfig

from apaFin.sender_telegram import SenderTelegram


class SenderTelegramTest(unittest.TestCase):

    @Mocker()
    def test_send_message(self, m: Mocker):
        config = StringConfig(string=json.dumps({"telegram": {"bot_token": "dummy_token", "receiver_ids": [123]}}))
        sender = SenderTelegram(config=config)

        mock_response = '''{
            "ok":true,
            "result":{
                "message_id":456,
                "from":{"id":1,"is_bot":true,"first_name":"Wohnbot","username":"wohnung_search_bot"},
                "chat":{"id":5,"first_name":"Arthur","last_name":"Taylor","type":"private"},
                "date":1589813130,
                "text":"hello arthur"
            }
        }'''
        m.post('https://api.telegram.org/botdummy_token/sendMessage', text=mock_response)
        self.assertIsNone(sender.notify("result"), "Expected message to be sent")

    @Mocker()
    def test_send_no_message_if_no_receivers(self, m: Mocker):
        config = StringConfig(string=json.dumps({"telegram": {"bot_token": "dummy_token", "receiver_ids": None}}))
        sender = SenderTelegram(config=config)
        self.assertEqual(None, sender.notify("result"), "Expected no message to be sent")

    @Mocker()
    def test_send_message_with_image(self, m: Mocker):
        c = StringConfig(string=json.dumps(
            {"telegram": {"bot_token": "dummy_token", "receiver_ids": [1234567], "notify_with_images": "true"}}
        ))
        sender = SenderTelegram(config=c)

        dummy_expose = {
            "title": "dummy title for test",
            "images": ["https://example.com"]
        }

        mock_message_response = '''{
            "ok":true,
            "result":{"message_id":456}
        }'''

        mock_media_group_response = '''{
            "ok":true,
            "result":{"message_id":456}
        }'''  # the response has been cut to keep the source code clean

        m.post('https://api.telegram.org/botdummy_token/sendMessage', text=mock_message_response)
        m.post('https://api.telegram.org/botdummy_token/sendMediaGroup', text=mock_media_group_response)

        self.assertTrue(sender.process_expose(expose=dummy_expose) == dummy_expose)

    @Mocker()
    def test_images_will_be_chunked(self, m: Mocker):
        c = StringConfig(string=json.dumps(
            {"telegram": {"bot_token": "dummy_token", "receiver_ids": [1234567], "notify_with_images": "true"}}
        ))

        sender = SenderTelegram(config=c)

        dummy_expose = {
            "title": "dummy title for test",
            "images": ["https://example.com" for _ in range(15)]
        }

        mock_message_response = '''{
                "ok":true,
                "result":{"message_id":456}
            }'''

        mock_media_group_response = '''{
                "ok":true,
                "result":{"message_id":456}
            }'''  # the response has been cut to keep the source code clean

        counter = RequestCounter()
        m.post('https://api.telegram.org/botdummy_token/sendMessage', text=mock_message_response)
        m.post('https://api.telegram.org/botdummy_token/sendMediaGroup',
               text=mock_media_group_response, additional_matcher=counter.count)

        exposed = sender.process_expose(expose=dummy_expose)

        self.assertEqual(2, counter.i)  # images is being sent in two messages.
        self.assertTrue(exposed == dummy_expose)
