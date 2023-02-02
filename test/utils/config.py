"""Wrap configuration options as an object"""
import yaml

from apaFin.config import YamlConfig, CaptchaEnvironmentConfig

class StringConfig(YamlConfig):
    """Class to represent apaFin configuration for tests"""

    def __init__(self, string=None):
        if string is not None:
            config = yaml.safe_load(string)
        else:
            config = {}
        super().__init__(config)

class StringConfigWithCaptchas(CaptchaEnvironmentConfig,StringConfig):
    """Class to represent apaFin configuration for tests, with captcha support"""
