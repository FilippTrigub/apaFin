""" Startup file for Google Cloud deployment or local webserver"""
import logging
import os

from apaFin.googlecloud_idmaintainer import GoogleCloudIdMaintainer
from apaFin.web_hunter import WebHunter
from apaFin.config import Config
from apaFin.logging import logger, wdm_logger, configure_logging

from apaFin.web import app

config = Config()

# Load the driver manager from local cache (if chrome_driver_install.py has been run
os.environ['WDM_LOCAL'] = '1'
# Use Google Cloud DB if we run on the cloud
id_watch = GoogleCloudIdMaintainer()

configure_logging(config)

# initialize search plugins for config
config.init_searchers()

hunter = WebHunter(config, id_watch)

hunter.hunt_flats()