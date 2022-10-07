import unittest

import requests_mock

from flathunter.sender_apprise import SenderApprise


class SenderAppriseTest(unittest.TestCase):

    @requests_mock.Mocker()
    def test_send_no_message_if_no_receivers(self, m):
        sender = SenderApprise({"apprise": []})
        self.assertEqual(None, sender.notify("result"), "Expected no message to be sent")
