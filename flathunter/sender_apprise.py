"""Functions and classes related to sending Apprise messages"""
import apprise

from flathunter.abstract_notifier import Notifier
from flathunter.abstract_processor import Processor


class SenderApprise(Processor, Notifier):
    """Expose processor that sends Apprise messages"""

    def __init__(self, config):
        self.config = config
        self.apprise_urls = self.config.get('apprise', {})

    def process_expose(self, expose):
        """Send a message to a user describing the expose"""
        message = self.config.get('message', "").format(
            title=expose['title'],
            rooms=expose['rooms'],
            size=expose['size'],
            price=expose['price'],
            url=expose['url'],
            address=expose['address'],
            durations="" if 'durations' not in expose else expose['durations']).strip()
        self.__send_msg(message)
        return expose

    def notify(self, message: str):
        """ Send the given message to users """
        self.__send_msg(message=message)

    def __send_msg(self, message):
        apobj = apprise.Apprise()
        """Send messages to each of the Apprise urls"""
        if self.apprise_urls is None:
            return
        for apprise_url in self.apprise_urls:
            apobj.add(apprise_url)

        apobj.notify(
            body=message,
            title='',
            body_format=apprise.NotifyFormat.TEXT,
        )
