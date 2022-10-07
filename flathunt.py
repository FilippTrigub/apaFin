#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flathunter - search for flats by crawling property portals, and receive telegram
   messages about them. This is the main command-line executable, for running on the
   console. To run as a webservice, look at main.py"""

import argparse
import os
import logging
import time

from flathunter.logging import logger, wdm_logger, configure_logging
from flathunter.idmaintainer import IdMaintainer
from flathunter.hunter import Hunter
from flathunter.config import Config, Env
from flathunter.heartbeat import Heartbeat

__author__ = "Jan Harrie"
__version__ = "1.0"
__maintainer__ = "Nody"
__email__ = "harrymcfly@protonmail.com"
__status__ = "Production"


def launch_flat_hunt(config, heartbeat=None):
    """Starts the crawler / notification loop"""
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')

    hunter = Hunter(config, id_watch)
    hunter.hunt_flats()
    counter = 0

    while config.loop_is_active():
        counter += 1
        counter = heartbeat.send_heartbeat(counter)
        time.sleep(config.loop_period_seconds())
        hunter.hunt_flats()


def main():
    """Processes command-line arguments, loads the config, launches the flathunter"""
    parser = argparse.ArgumentParser(
        description=("Searches for flats on Immobilienscout24.de and wg-gesucht.de"
                     " and sends results to Telegram User"),
        epilog="Designed by Nody"
    )
    if Env.FLATHUNTER_TARGET_URLS is not None:
        default_config_path = None
    else:
        default_config_path = f"{os.path.dirname(os.path.abspath(__file__))}/config.yaml"
    parser.add_argument('--config', '-c',
                        type=argparse.FileType('r', encoding='UTF-8'),
                        default=default_config_path,
                        help=f'Config file to use. If not set, try to use "{default_config_path}"'
                        )
    parser.add_argument('--heartbeat', '-hb',
                        action='store',
                        default=None,
                        help=('Set the interval time to receive heartbeat messages to check'
                              'that the bot is alive. Accepted strings are "hour", "day", "week".'
                              'Defaults to None.')
                        )
    args = parser.parse_args()

    # load config
    config_handle = args.config
    if config_handle is not None:
        config = Config(config_handle.name)
    else:
        config = Config()

    # setup logging
    configure_logging(config)

    # initialize search plugins for config
    config.init_searchers()

    # check config
    notifiers = config.notifiers()
    if 'mattermost' in notifiers \
            and not config.mattermost_webhook_url():
        logger.error("No Mattermost webhook configured. Starting like this would be pointless...")
        return
    if 'telegram' in notifiers:
        if not config.telegram_bot_token():
            logger.error(
                "No Telegram bot token configured. Starting like this would be pointless..."
            )
            return
        if len(config.telegram_receiver_ids()) == 0:
            logger.warning("No Telegram receivers configured - nobody will get notifications.")
    if 'apprise' in notifiers \
            and not config.get('apprise', {}):
        logger.error("No apprise url configured. Starting like this would be pointless...")
        return

    if len(config.target_urls()) == 0:
        logger.error("No URLs configured. Starting like this would be pointless...")
        return

    # get heartbeat instructions
    heartbeat_interval = args.heartbeat
    heartbeat = Heartbeat(config, heartbeat_interval)

    # start hunting for flats
    launch_flat_hunt(config, heartbeat)


if __name__ == "__main__":
    main()
