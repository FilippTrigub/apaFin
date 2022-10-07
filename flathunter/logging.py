"""Provides logger"""
import logging
import os
from pprint import pformat


class LoggerHandler(logging.StreamHandler):
    """Formats logs and alters WebDriverManager's logs properties"""

    _CYELLOW = '\033[93m' if os.name == 'posix' else ''
    _CBLUE = '\033[94m' if os.name == 'posix' else ''
    _COFF = '\033[0m' if os.name == 'posix' else ''
    _FORMAT = '[' + _CBLUE + '%(asctime)s' + _COFF + \
              '|' + _CBLUE + '%(filename)-24s' + _COFF + \
              '|' + _CYELLOW + '%(levelname)-8s' + _COFF + \
              ']: %(message)s'
    _DATE_FORMAT = '%Y/%m/%d %H:%M:%S'

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(
            fmt=self._FORMAT,
            datefmt=self._DATE_FORMAT
        ))

    def emit(self, record):
        # Log record came from webdriver-manager logger
        if record.name == "WDM":
            # Filename to display in log
            record.filename = "<WebDriverManager>"
            # Always display loglevel as DEBUG
            record.levelname = "DEBUG"
        super().emit(record)


def setup_wdm_logger(wdm_new_logger_handler):
    """Setup "webdriver-manager" module's logger"""
    wdm_log = logging.getLogger('WDM')
    # Only allow critical-level logs by default (mute)
    wdm_log.setLevel(logging.CRITICAL)
    wdm_log.propagate = False
    # wdm_log.removeHandler(wdm_logger_handler)
    wdm_log.addHandler(wdm_new_logger_handler)
    return wdm_log


# Setup Flathunter logger
logger_handler = LoggerHandler()
logging.basicConfig(level=logging.INFO, handlers=[logger_handler])
logger = logging.getLogger('flathunt')

# Setup "webdriver-manager" module's logger
wdm_logger = setup_wdm_logger(logger_handler)

# Setup "requests" module's logger
logging.getLogger("requests").setLevel(logging.WARNING)

def configure_logging(config):
    if config.verbose_logging():
        logger.setLevel(logging.DEBUG)
        # Allow logging of "webdriver-manager" module on verbose mode
        wdm_logger.setLevel(logging.INFO)
    logger.debug("Settings from config: %s", pformat(config))