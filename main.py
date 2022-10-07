""" Startup file for Google Cloud deployment or local webserver"""
import logging
import os

from flathunter.idmaintainer import IdMaintainer
from flathunter.googlecloud_idmaintainer import GoogleCloudIdMaintainer
from flathunter.web_hunter import WebHunter
from flathunter.config import Config
from flathunter.logging import logger, wdm_logger, configure_logging

from flathunter.web import app

config = Config()

if __name__ == '__main__':
    # Use the SQLite DB file if we are running locally
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
else:
    # Load the driver manager from local cache (if chrome_driver_install.py has been run
    os.environ['WDM_LOCAL'] = '1'
    # Use Google Cloud DB if we run on the cloud
    id_watch = GoogleCloudIdMaintainer()

configure_logging(config)

# initialize search plugins for config
config.init_searchers()

hunter = WebHunter(config, id_watch)

app.config["HUNTER"] = hunter
if config.has_website_config():
    app.secret_key = config.website_session_key()
    app.config["DOMAIN"] = config.website_domain()
    app.config["BOT_NAME"] = config.website_bot_name()
else:
    app.secret_key = b'Not a secret'
notifiers = config.notifiers()
if "telegram" in notifiers:
    app.config["BOT_TOKEN"] = config.telegram_bot_token()
if "mattermost" in notifiers:
    app.config["MM_WEBHOOK_URL"] = config.mattermost_webhook_url()

if __name__ == '__main__':
    listen = config['website'].get('listen', {})
    host = listen.get('host', '127.0.0.1')
    port = listen.get('port', '8080')
    app.run(host=host, port=port, debug=True)
