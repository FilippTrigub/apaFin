# ApaFin

For those, who are wary of searching for apartments in Berlin. This bot will find them and automatically apply to them until you can call one of them home.

## Description

ApaFin searches the usual websites for new offers based on your filters, attempts to automatically apply if enabled and messages you the status and details of the application via telegram.

## Table of Contents
- [Background](#background)
- [Install](#install)
- [Configuration](#configuration)
- [Contributions](#contributions)

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

### Configuration

Before running the project for the first time, copy `config.yaml.dist` to `config.yaml`. The `urls` and `telegram` sections of the config file must be configured according to your requirements before the project will run. 

### Contributions

This repo is a fork of the flathunter repo with adaptation for automatic application made by @PhilTrigu .