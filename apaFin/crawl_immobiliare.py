"""Expose crawler for Immobiliare"""
import re

from apaFin.logging import logger
from apaFin.abstract_crawler import Crawler

class CrawlImmobiliare(Crawler):
    """Implementation of Crawler interface for Immobiliare"""

    URL_PATTERN = re.compile(r'https://www\.immobiliare\.it')

    def __init__(self, config):
        super().__init__(config)
        self.config = config

    # pylint: disable=too-many-locals
    def extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []

        findings = soup.find_all(lambda e: e.has_attr('data-id') \
            and e.has_attr('class') \
            and "listing-item" in e['class'])

        for row in findings:
            title_row = row.find('p', {"class": "titolo text-primary"})
            title = title_row.text.strip()
            url = title_row.find('a')['href']
            image_item = row.find('div', {"class": "showcase__item"})
            image = image_item.find('img')['src'] if image_item else ""

            # the items arrange like so:
            # 0: price
            # 1: number of rooms
            # 2: size of the apartment
            price_li = row.find("li", {"class": "lif__pricing"})

            price = re.match(
                r".*\s([0-9]+.*)$",
                # if there is a discount on the price, then there will be a <div>,
                # otherwise the text we are looking for is directly inside the <li>
                (price_li.find("div") if price_li.find("div") else price_li).text.strip()
            )[1]

            details_list = row.find_all("li", {"class": "lif__item"})

            rooms = details_list[1].find("span").text.strip() if len(details_list) > 1 else "?"
            size = details_list[2].find("span").text.strip() if len(details_list) > 2 else "?"

            address_match = re.match(r"\w+\s(.*)$", title)
            address = address_match[1] if address_match else ""

            details = {
                'id': int(row['data-id']),
                'image': image,
                'url': url,
                'title': title,
                'price': price,
                'size': size,
                'rooms': rooms,
                'address': address,
                'crawler': self.get_name()
            }

            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries
