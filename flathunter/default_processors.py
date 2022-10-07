"""Built-in expose processor implementations. Used by the processor pipelines
   in flathunter and in the webservice"""
import re

from flathunter.logging import logger
from flathunter.abstract_processor import Processor

class Filter(Processor):
    """Filter processor implementation. Applies a filter to the list of exposes"""

    def __init__(self, config, filter_set):
        self.config = config
        self.filter = filter_set

    def process_exposes(self, exposes):
        return self.filter.filter(exposes)

class AddressResolver(Processor):
    """Processor to extract apartment addresses from expose links"""

    def __init__(self, config):
        self.config = config

    def process_expose(self, expose):
        """Fetches the expose from the expose URL and extracts the address"""
        if expose['address'].startswith('http'):
            url = expose['address']
            for searcher in self.config.searchers():
                if re.search(searcher.URL_PATTERN, url):
                    expose['address'] = searcher.load_address(url)
                    logger.debug("Loaded address %s for url %s", expose['address'], url)
                    break
        return expose

class CrawlExposeDetails(Processor):
    """Processor to extract additional apartment details by parsing page at expose URL"""

    def __init__(self, config):
        self.config = config

    def process_expose(self, expose):
        """Fetches the page at exposes['url'] and extracts additional details from it"""
        for searcher in self.config.searchers():
            if re.search(searcher.URL_PATTERN, expose['url']):
                expose = searcher.get_expose_details(expose)
        return expose

class LambdaProcessor(Processor):
    """Processor to apply arbitrary logic to each expose"""

    def __init__(self, config, func):
        self.config = config
        self.func = func

    def process_expose(self, expose):
        """Apply the lambda function to each expose"""
        res = self.func(expose)
        return res
