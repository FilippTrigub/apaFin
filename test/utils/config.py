"""Wrap configuration options as an object"""
import yaml

from flathunter.config import YamlConfig, CaptchaEnvironmentConfig

class StringConfig(YamlConfig):
    """Class to represent flathunter configuration for tests"""

    def __init__(self, string=None):
        if string is not None:
            config = yaml.safe_load(string)
        else:
            config = {}
        super().__init__(config)

class StringConfigWithCaptchas(CaptchaEnvironmentConfig,StringConfig):
    """Class to represent flathunter configuration for tests, with captcha support"""
