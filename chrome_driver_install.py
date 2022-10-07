import logging
import os

from flathunter.logging import wdm_logger
from webdriver_manager.chrome import ChromeDriverManager

# Cache the driver manager to local folder so that gunicorn can find it
os.environ['WDM_LOCAL'] = '1'
wdm_logger.setLevel(logging.INFO)

ChromeDriverManager().install()
