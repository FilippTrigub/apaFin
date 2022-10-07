"""Module with implementations of standard expose filters"""
from functools import reduce
import re

from flathunter.idmaintainer import AlreadySeenFilter

class ExposeHelper:
    """Helper functions for extracting data from expose text"""

    @staticmethod
    def get_price(expose):
        """Extracts the price from a price text"""
        price_match = re.search(r'\d+([\.,]\d+)?', expose['price'])
        if price_match is None:
            return None
        return float(price_match[0].replace(".", "").replace(",", "."))

    @staticmethod
    def get_size(expose):
        """Extracts the size from a size text"""
        size_match = re.search(r'\d+([\.,]\d+)?', expose['size'])
        if size_match is None:
            return None
        return float(size_match[0].replace(",", "."))

    @staticmethod
    def get_rooms(expose):
        """Extracts the number of rooms from a room text"""
        rooms_match = re.search(r'\d+([\.,]\d+)?', expose['rooms'])
        if rooms_match is None:
            return None
        return float(rooms_match[0].replace(",", "."))

class MaxPriceFilter:
    """Exclude exposes above a given price"""

    def __init__(self, max_price):
        self.max_price = max_price

    def is_interesting(self, expose):
        """True if expose is below the max price"""
        price = ExposeHelper.get_price(expose)
        if price is None:
            return True
        return price <= self.max_price

class MinPriceFilter:
    """Exclude exposes below a given price"""

    def __init__(self, min_price):
        self.min_price = min_price

    def is_interesting(self, expose):
        """True if expose is above the min price"""
        price = ExposeHelper.get_price(expose)
        if price is None:
            return True
        return price >= self.min_price

class MaxSizeFilter:
    """Exclude exposes above a given size"""

    def __init__(self, max_size):
        self.max_size = max_size

    def is_interesting(self, expose):
        """True if expose is below the max size"""
        size = ExposeHelper.get_size(expose)
        if size is None:
            return True
        return size <= self.max_size

class MinSizeFilter:
    """Exclude exposes below a given size"""

    def __init__(self, min_size):
        self.min_size = min_size

    def is_interesting(self, expose):
        """True if expose is above the min size"""
        size = ExposeHelper.get_size(expose)
        if size is None:
            return True
        return size >= self.min_size

class MaxRoomsFilter:
    """Exclude exposes above a given number of rooms"""

    def __init__(self, max_rooms):
        self.max_rooms = max_rooms

    def is_interesting(self, expose):
        """True if expose is below the max number of rooms"""
        rooms = ExposeHelper.get_rooms(expose)
        if rooms is None:
            return True
        return rooms <= self.max_rooms

class MinRoomsFilter:
    """Exclude exposes below a given number of rooms"""

    def __init__(self, min_rooms):
        self.min_rooms = min_rooms

    def is_interesting(self, expose):
        """True if expose is above the min number of rooms"""
        rooms = ExposeHelper.get_rooms(expose)
        if rooms is None:
            return True
        return rooms >= self.min_rooms

class TitleFilter:
    """Exclude exposes whose titles match the provided terms"""

    def __init__(self, filtered_titles):
        self.filtered_titles = filtered_titles

    def is_interesting(self, expose):
        """True unless title matches the filtered titles"""
        combined_excludes = "(" + ")|(".join(self.filtered_titles) + ")"
        found_objects = re.search(combined_excludes, expose['title'], re.IGNORECASE)
        # send all non matching regex patterns
        if not found_objects:
            return True
        return False

class PPSFilter:
    """Exclude exposes above a given price per square"""

    def __init__(self, max_pps):
        self.max_pps = max_pps

    def is_interesting(self, expose):
        """True if price per square is below max price per square"""
        size = ExposeHelper.get_size(expose)
        price = ExposeHelper.get_price(expose)
        if size is None or price is None:
            return True
        pps = price / size
        return pps <= self.max_pps

class PredicateFilter:
    """Include only those exposes satisfying the predicate"""

    def __init__(self, predicate):
        self.predicate = predicate

    def is_interesting(self, expose):
        """True if predicate is satisfied"""
        return self.predicate(expose)

class FilterBuilder:
    """Construct a filter chain"""

    def __init__(self):
        self.filters = []

    def read_config(self, config):
        """Adds filters from a config dictionary"""
        if "excluded_titles" in config:
            self.filters.append(TitleFilter(config["excluded_titles"]))
        if "filters" in config and config["filters"] is not None:
            filters_config = config["filters"]
            if "excluded_titles" in filters_config:
                self.filters.append(TitleFilter(filters_config["excluded_titles"]))
            if "min_price" in filters_config:
                self.filters.append(MinPriceFilter(filters_config["min_price"]))
            if "max_price" in filters_config:
                self.filters.append(MaxPriceFilter(filters_config["max_price"]))
            if "min_size" in filters_config:
                self.filters.append(MinSizeFilter(filters_config["min_size"]))
            if "max_size" in filters_config:
                self.filters.append(MaxSizeFilter(filters_config["max_size"]))
            if "min_rooms" in filters_config:
                self.filters.append(MinRoomsFilter(filters_config["min_rooms"]))
            if "max_rooms" in filters_config:
                self.filters.append(MaxRoomsFilter(filters_config["max_rooms"]))
            if "max_price_per_square" in filters_config:
                self.filters.append(PPSFilter(filters_config["max_price_per_square"]))
        return self

    def max_size_filter(self, size):
        """Adds a max size filter"""
        self.filters.append(MaxSizeFilter(size))
        return self

    def predicate_filter(self, predicate):
        """Adds a predicate filter"""
        self.filters.append(PredicateFilter(predicate))
        return self

    def filter_already_seen(self, id_watch):
        """Filter exposes that have already been seen"""
        self.filters.append(AlreadySeenFilter(id_watch))
        return self

    def build(self):
        """Return the compiled filter"""
        return Filter(self.filters)

class Filter:
    """Abstract filter object"""

    def __init__(self, filters):
        self.filters = filters

    def is_interesting_expose(self, expose):
        """Apply all filters to this expose"""
        return reduce((lambda x, y: x and y),
                      map((lambda x: x.is_interesting(expose)), self.filters), True)

    def filter(self, exposes):
        """Apply all filters to every expose in the list"""
        return filter(self.is_interesting_expose, exposes)

    @staticmethod
    def builder():
        """Return a new filter builder"""
        return FilterBuilder()
