# Flathunter

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat)](https://github.com/RichardLitt/standard-readme)
[![Lint Code Base](https://github.com/flathunters/flathunter/actions/workflows/linter.yml/badge.svg)](https://github.com/flathunters/flathunter/actions/workflows/linter.yml)
[![Tests](https://github.com/flathunters/flathunter/actions/workflows/tests.yml/badge.svg)](https://github.com/flathunters/flathunter/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/flathunters/flathunter/branch/master/graph/badge.svg)](https://codecov.io/gh/flathunters/flathunter)

A bot to help people with their rental real-estate search. 🏠🤖

## Description

Flathunter is a Python application which periodically [scrapes](https://en.wikipedia.org/wiki/Web_scraping) property listings sites, configured by the user, to find new rental real-estate listings, reporting them over messaging services.

Currently available messaging services are [Telegram](https://telegram.org/), [Mattermost](https://mattermost.com/) and [Apprise](https://github.com/caronc/apprise).

## Table of Contents
- [Background](#background)
- [Install](#install)
  - [Prerequisites](#prerequisites)
  - [Installation on Linux](#installation-on-linux)
- [Usage](#usage)
  - [Configuration](#configuration)
    - [URLs](#urls)
    - [Telegram](#telegram)
    - [2Captcha](#2captcha)
    - [Proxy](#proxy)
    - [Google API](#google-api)
  - [Command-line Interface](#command-line-interface)
  - [Web Interface](#web-interface)
  - [Docker](#docker)
  - [Google Cloud Deployment](#google-cloud-deployment)
- [Testing](#testing)
- [Maintainers](#maintainers)
- [Credits](#credits)
  - [Contributers](#contributers)
- [Contributing](#contributing)

## Background

There are at least four different rental property marketplace sites that are widely used in Germany - [ImmoScout24](https://www.immobilienscout24.de/), [Immowelt](https://www.immowelt.de/), [WG-Gesucht](https://www.wg-gesucht.de/) and [eBay Kleinanzeigen](https://www.ebay-kleinanzeigen.de/). Most people end up searching through listings on all four sites on an almost daily basis during their rental search.
In Italy on the other hand, [idealista](https://www.idealista.it), [Subito](https://www.subito.it) and [Immobiliare.it](https://www.immobiliare.it) are very common for real-estate hunting.

With ```Flathunter```, instead of visiting the same pages on the same  sites every day, you can set the system up to scan every site, filtering by your search criteria, and notify you when new rental property becomes available that meets your criteria.

## Prerequisites
* [Python 3.8+](https://www.python.org/)
* [pipenv](https://pipenv.pypa.io/en/latest/)
* [Docker]() (*optional*)
* [GCloud CLI]() (*optional*)

## Install

Start by installing all dependencies inside a virtual environment using ```pipenv``` from the project's directory:

```sh
$ pipenv install
```

Once the dependencies are installed, as well as every time you come back to the project in a new shell, run:

```sh
$ pipenv shell
```

to launch a Python environment with the dependencies that your project requires. **Now that you are inside the virtual environment, you can start the actual program:**

```sh
$ python flathunt.py
```

**To directly run the program without entering the venv first, use:**

```sh
$ pipenv run python flathunt.py
```

For development purposes, you need to install the flathunter module in your current environment. Simply run:

```sh
$ pip install -e .
```

### Installation on Linux
(tested on CentOS Stream)

First clone the repository
```sh
$ cd /opt
$ git clone https://github.com/flathunters/flathunter.git
```
add a new User and configure the permissions
```sh
$ useradd flathunter
$ chown flathunter:flathunter -R flathunter/
```
Next install pipenv for the new user
```sh
$ sudo -u flathunter pip install --user pipenv
$ cd flathunter/
$ sudo -u flathunter /home/flathunter/.local/bin/pipenv install
```
Next configure the config file and service file to your liking. Then move the service file in place:
```sh
$ mv flathunter/sample-flathunter.service /lib/systemd/system/flathunter.service
```
At last you just have to start flathunter
```sh
$ systemctl enable flathunter --now
```
If you're using SELinux the following policy needs to be added:
```sh
$ chcon -R -t bin_t /home/flathunter/.local/bin/pipenv
```

## Usage

### Configuration

Before running the project for the first time, copy `config.yaml.dist` to `config.yaml`. The `urls` and `telegram` sections of the config file must be configured according to your requirements before the project will run. 

#### URLs

To configure the searches, simply visit the property portal of your choice (e.g. ImmoScout24), configure the search on the website to match your search criteria, then copy the URL of the results page into the config file. You can add as many URLs as you like, also multiple from the same website if you have multiple different criteria (e.g. running the same search in different areas).

 * Currently, eBay Kleinanzeigen, Immowelt, WG-Gesucht and Idealista only crawl the first page, so make sure to **sort by newest offers**.
 * Your links should point to the German version of the websites (in the case of eBay Kleinanzeigen, Immowelt, ImmoScout24 and WG-Gesucht), since it is tested only there. Otherwise you might have problems.
 * For Idealista, the link should point to the Italian version of the website, for the same reason reported above.
 * For Immobiliare, the link should point to the Italian version of the website, for the same reasons reported above.
 * For Subito, the link should point to the Italian version of the website, for the same reasons reported above.

#### Telegram

To be able to send messages to you over Telegram, you need to register a new bot with the [BotFather](https://telegram.me/BotFather) for `Flathunter` to use. Through this process, a "Bot Token" will be created for you, which should be configured under `bot_token` in the config file.

To know who should Telegram messages should be sent to, the "Chat IDs" of the recipients must be added to the config file under `receiver_ids`. To work out your own Chat ID, send a message to your new bot, then run:

```
$ curl https://api.telegram.org/bot[BOT-TOKEN]/getUpdates
```

to get list of messages the Bot has received. You will see your Chat ID in there.

#### 2Captcha

Some sites (including ImmoScout24) implement Captcha to avoid being crawled by evil web scrapers. Since our crawler is not an evil one, the people at [2Captcha](https://2captcha.com) provide us a service that helps you solve them. Head to the `2Captcha` website, register and pay 3$ for 1000 solved captchas! Check the `config.yaml.dist` on how to configure `2Captcha` with Flathunter. **At this time, ImmoScout24 can not be crawled by Flathunter without using 2Captcha**.

#### Proxy

It's common that websites use bots and crawler protections to avoid being flooded with possibly malicious traffic. This can cause some issues when crawling, as we will be presented with a bot-protection page.
To circumvent this, we can enable proxies with the configuration key `use_proxy_list` and setting it to `True`.
Flathunt will crawl a [free-proxy list website](https://free-proxy-list.net/) to retrieve a list of possible proxies to use, and cycle through the so obtained list until an usable proxy is found.  
*Note*: there may be a lot of attemps before such an usable proxy is found. Depending on your region or your server's internet accessibility, it can take a while.

#### Google API

To use the distance calculation feature a [Google API-Key](https://developers.google.com/maps/documentation/javascript/get-api-key) is needed, as well as to enable the [Distance Matrix API](https://developers.google.com/maps/documentation/distance-matrix/overview) (This is NOT free).

### Command-line Interface

By default, the application runs on the commandline and outputs logs to `stdout`. It will poll in a loop and send updates after each run. The `processed_ids.db` file contains details of which listings have already been sent to the Telegram bot - if you delete that, it will be recreated, and you may receive duplicate listings.

```
usage: flathunt.py [-h] [--config CONFIG]

Searches for flats on Immobilienscout24.de and wg-gesucht.de and sends results
to Telegram User

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Config file to use. If not set, try to use
                        '~git-clone-dir/config.yaml'
  --heartbeat INTERVAL, -hb INTERVAL
			Set the interval time to receive heartbeat messages to check that the bot is
                        alive. Accepted strings are "hour", "day", "week". Defaults to None.
```

### Web Interface

You can alternatively launch the web interface by running the `main.py` application:

```
$ python main.py
```

This uses the same config file as the Command-line Interface, and launches a web page at [http://localhost:8080](http://localhost:8080).

Alternatively, run the server directly with Flask:

```
$ FLASK_APP=flathunter.web flask run
```

### Docker

First build the image inside the project's root directory:
```sh
$ docker build -t flathunter .
```

**When running a container using the image, a config file needs to be mounted on the container at ```/config.yaml``` or configuration has to be supplied using environment variables.** The example below provides the file ```config.yaml``` off the current working directory:

```sh
$ docker run --mount type=bind,source=$PWD/config.yaml,target=/config.yaml flathunter
```

#### Environment Configuration

To make deployment with docker easier, most of the important configuration options can be set with environment variables. The current list of recognised variables includes:

 - FLATHUNTER_TARGET_URLS - a semicolon-separated list of URLs to crawl
 - FLATHUNTER_DATABASE_LOCATION - the location on disk of the sqlite database if required
 - FLATHUNTER_GOOGLE_CLOUD_PROJECT_ID - the Google Cloud Project ID, for Google Cloud deployments
 - FLATHUNTER_VERBOSE_LOG - set to any value to enable verbose logging
 - FLATHUNTER_LOOP_PERIOD_SECONDS - a number in seconds for the crawling interval
 - FLATHUNTER_MESSAGE_FORMAT - a format string for the notification messages, where `#CR#` will be replaced by newline
 - FLATHUNTER_NOTIFIERS - a comma-separated list of notifiers to enable (e.g. `telegram,mattermost`)
 - FLATHUNTER_TELEGRAM_BOT_TOKEN - the token for the Telegram notifier
 - FLATHUNTER_TELEGRAM_RECEIVER_IDS - a comma-separated list of receiver IDs for Telegram notifications
 - FLATHUNTER_MATTERMOST_WEBHOOK_URL - the webhook URL for Mattermost notifications
 - FLATHUNTER_WEBSITE_SESSION_KEY - the secret session key used to secure sessions for the flathunter website deployment
 - FLATHUNTER_WEBSITE_DOMAIN - the public domain of the flathunter website deployment
 - FLATHUNTER_2CAPTCHA_KEY - the API key for 2captcha
 - FLATHUNTER_IMAGETYPERZ_TOKEN - the API token for ImageTyperz
 - FLATHUNTER_HEADLESS_BROWSER - set to any value to configure Google Chrome to be launched in headless mode (necessary for Docker installations)

### Google Cloud Deployment

You can run `Flathunter` on Google's App Engine, in the free tier, at no cost if you don't need captcha solving. If you need to solve captchas, you can use Google Cloud Run as described later. To get started, first install the [Google Cloud SDK](https://cloud.google.com/sdk/docs) on your machine, and run:

```
$ gcloud init
```

to setup the SDK. You will need to create a new cloud project (or connect to an existing project). The Flathunters organisation uses the `flathunters` project ID to deploy the application. If you need access to deploy to that project, contact the maintainers.

```
$ gcloud config set project flathunters
```

You will need to provide the project ID to the configuration file `config.yaml` as value to the key `google_cloud_project_id` or in the `FLATHUNTER_GOOGLE_CLOUD_PROJECT_ID` environment variable.

Google Cloud [doesn't currently support Pipfiles](https://stackoverflow.com/questions/58546089/does-google-app-engine-flex-support-pipfile). To work around this restriction, the `Pipfile` and `Pipfile.lock` have been added to `.gcloudignore`, and a `requirements.txt` file has been generated using `pip freeze`. 

If the Pipfile has been updated, you will need to remove the line `pkg-resources==0.0.0` from `requirements.txt` for a successful deploy.

#### Google App Engine Deployment

To deploy the app to Google App Engine, run:

```
$ gcloud app deploy
```

Your project will need to have the [Cloud Build API](https://console.developers.google.com/apis/api/cloudbuild.googleapis.com/overview) enabled, which requires it to be linked to a billing-enabled account. It also needs [Cloud Firestore API](https://console.cloud.google.com/apis/library/firestore.googleapis.com) to be enabled for the project. Firestore needs to be configured in [Native mode](https://cloud.google.com/datastore/docs/upgrade-to-firestore).

Instead of running with a timer, the web interface depends on periodic calls to the `/hunt` URL to trigger searches (this avoids the need to have a long-running process in the on-demand compute environment). You can configure Google Cloud to automatically hit the URL by deploying the cron job:

```
$ gcloud app deploy cron.yaml
```

#### Google Cloud Run Deployment

If you need captcha support (for example to scrape Immoscout), you will need to deploy using [Google Cloud Run](https://cloud.google.com/run/), so that you can embed the Chrome browser and Selenium Webdriver in the docker image. A seperate `Dockerfile.gcloud.job` exists for this purpose.

First, ensure that `requirements.txt` has been created (per [Google Cloud Deployment](#google-cloud-deployment)), then either run:

```
docker build -t flathunter-job -f Dockerfile.gcloud.job .
```

to build the docker image locally, or edit the `cloudbuild.yaml` file to point to the container registry for your own Google Cloud Project, and run:

```
gcloud builds submit --region=europe-west1
```

to have [Google Cloud Build](https://cloud.google.com/build) build and tag the image for you.

You will need to create a new [Google Cloud Run Job](https://console.cloud.google.com/run/jobs) to execute the crawl/notify. The job should be configured with 1GB of memory and 1 CPU, and the environment variables to should be set appropriately.

You can trigger the job using [Google Cloud Scheduler](https://console.cloud.google.com/cloudscheduler), using an HTTP POST to:

```
https://[REGION]-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/[PROJECT_ID]/jobs/[JOB_NAME]:run
```

For more information checkout [the Cloud Scheduler documentation](https://cloud.google.com/run/docs/execute/jobs-on-schedule).

Because the image uses Firestore to read details of user notification preferences and store crawled exposes, the job can run without any additional configuration. If you are hosting the webinterface somewhere on Google Cloud (either App Engine or Google Cloud Run), the job here will find the appropriate Firebase database.

## Testing

The test suite can be run with `pytest`:

```sh
$ pytest
```

from the project root. If you encounter the error `ModuleNotFoundError: No module named 'flathunter'`, run:

```sh
$ pip install -e .
```

to make the current project visible to your pip environment.

## Maintainers

This project is maintained by the members of the [Flat Hunters](https://github.com/flathunters) Github organisation, which is a collection of individual unpaid volunteers who have all had their own processes with flat-hunting in Germany. If you want to join, just ping one of us a message!

## Credits

The original code was contributed by [@NodyHub](https://github.com/NodyHub), whose original idea this project was.

### Contributers

Other contributions were made along the way by:

- Bene
- [@tschuehly](https://github.com/tschuehly)
- [@Cugu](https://github.com/Cugu)
- [@GerRudi](https://github.com/GerRudi)
- [@xMordax](https://github.com/xMordax)
- [@codders](https://github.com/codders)
- [@alexanderroidl](https://github.com/alexanderroidl)

## Contributing

If you want to make a contribution, please check out the contributor code of conduct ([EN 🇬🇧](CODE_OF_CONDUCT.en.md)/[DE 🇩🇪](CODE_OF_CONDUCT.de.md)) first. Pull requests are very welcome, as are [issues](https://github.com/flathunters/flathunter/issues). If you file an issue, please include as much information as possible about how to reproduce the issue.
