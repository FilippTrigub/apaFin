# ApaFin

For those, who are wary of searching for apartments in Berlin. This bot will find them and automatically apply to them until you can call one of them home.

## Description

ApaFin searches the usual websites for new offers based on your filters, attempts to automatically apply if enabled and messages you the status and details of the application via telegram.

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

## Motivation

Rental websites are made for landlords, not tenants. ApaFin allows to avoid the pain incurred searching for a place to live.

## Prerequisites
* [Python 3.8+](https://www.python.org/)
* [pipenv](https://pipenv.pypa.io/en/latest/)
* [Docker]() (*optional*)
* [GCloud CLI]() (*optional*)

## Install

Install the dependencies executing the following command in the root directory of the project. 

```sh
$ pipenv install
```

**The run**

```sh
$ pipenv run python flathunt.py
```

## Usage

### Configuration

Before running the project for the first time, copy `config.yaml.dist` to `config.yaml`. The `urls` and `telegram` sections of the config file must be configured according to your requirements before the project will run. 
