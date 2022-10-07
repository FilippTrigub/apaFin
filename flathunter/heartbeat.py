"""Providing heartbeat messages"""
from typing import Union

from flathunter.abstract_notifier import Notifier
from flathunter.config import Config
from flathunter.logging import logger
from flathunter.sender_apprise import SenderApprise
from flathunter.sender_mattermost import SenderMattermost
from flathunter.sender_telegram import SenderTelegram


def interval2counter(interval: str) -> Union[None, int]:
    """Transform the string interval to sleeper counter frequencies"""
    if interval is None:
        return None
    if interval.lower() == 'hour':
        return 6
    if interval.lower() == 'day':
        return 144
    if interval.lower() == 'week':
        return 1008
    raise Exception("No valid heartbeat instruction received - no heartbeat messages will be sent.")


class Heartbeat:
    """Will inform the user on regular intervals whether the bot is still alive"""
    __notifier: Notifier
    __interval: int
    __config: Config

    def __init__(self, config: Config, interval: str):
        self.config = config
        notifiers = self.config.notifiers()

        if 'mattermost' in notifiers:
            self.__notifier = SenderMattermost(config)
        elif 'telegram' in notifiers:
            self.__notifier = SenderTelegram(config)
        elif 'apprise' in notifiers:
            self.__notifier = SenderApprise(config)

        self.__interval = interval2counter(interval)

    def send_heartbeat(self, counter) -> int:
        """Send a new heartbeat message"""
        if not self.__notifier or not self.__interval:  # interval is disabled
            return counter
        # it's time for a new heartbeat message and reset counter
        if counter % self.__interval == 0:
            logger.info('Sending heartbeat message.')
            self.__notifier.notify(
                'Beep Boop. This is a heartbeat message. '
                'Your bot is searching actively for flats.'
            )
            counter = 0
        return counter
