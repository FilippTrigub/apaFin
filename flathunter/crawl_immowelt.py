"""Expose crawler for ImmoWelt"""
import re
import datetime
import hashlib
import time
import traceback

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from flathunter.logging import logger
from flathunter.abstract_crawler import Crawler, CaptchaNotFound, ApplicationUnsuccesfulException


class CrawlImmowelt(Crawler):
    """Implementation of Crawler interface for ImmoWelt"""

    URL_PATTERN = re.compile(r'https://www\.immowelt\.de')

    MODULE_NAME = 'immowelt'

    def __init__(self, config):
        super().__init__(config)
        self.initialize_driver()

    def get_expose_details(self, expose):
        """Loads additional details for an expose by processing the expose detail URL"""
        soup = self.get_page(expose['url'])
        date = datetime.datetime.now().strftime("%2d.%2m.%Y")

        immo_div = soup.find("app-estate-object-informations")
        if immo_div is not None:
            immo_div = soup.find("div", {"class": "equipment ng-star-inserted"})
            if immo_div is not None:
                details = immo_div.find_all("p")

                for detail in details:
                    if detail.text.strip() == "Bezug":
                        date = detail.findNext("p").text.strip()
                        no_exact_date_given = re.match(
                            r'.*sofort.*|.*Nach Vereinbarung.*',
                            date,
                            re.MULTILINE | re.DOTALL | re.IGNORECASE
                        )
                        if no_exact_date_given:
                            date = datetime.datetime.now().strftime("%2d.%2m.%Y")
                        break
        expose['from'] = date
        return expose

    # pylint: disable=too-many-locals
    def extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []
        soup = soup.find("main")

        try:
            title_elements = soup.find_all("h2")
        except AttributeError:
            return entries
        expose_ids = soup.find_all("a", id=True)

        for idx, title_el in enumerate(title_elements):
            try:
                price = expose_ids[idx].find(
                    "div", attrs={"data-test": "price"}).text
            except IndexError:
                price = ""

            try:
                size = expose_ids[idx].find(
                    "div", attrs={"data-test": "area"}).text
            except IndexError:
                size = ""

            try:
                rooms = expose_ids[idx].find(
                    "div", attrs={"data-test": "rooms"}).text
            except IndexError:
                rooms = ""

            url = expose_ids[idx].get("href")

            picture = expose_ids[idx].find("picture")
            image = None
            if picture:
                src = picture.find("source")
                if src:
                    image = src.get("data-srcset")

            try:
                address = expose_ids[idx].find(
                    "div", attrs={"class": re.compile("IconFact.*")}
                )
                address = address.find("span").text
            except IndexError:
                address = ""

            processed_id = int(
                hashlib.sha256(expose_ids[idx].get("id").encode('utf-8')).hexdigest(), 16
            ) % 10 ** 16

            details = {
                'id': processed_id,
                'image': image,
                'url': url,
                'title': title_el.text.strip(),
                'rooms': rooms,
                'price': price,
                'size': size,
                'address': address,
                'crawler': self.get_name()
            }
            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries

    # pylint: disable=unused-argument
    def get_results(self, search_url, max_pages=None):
        """Loads the exposes from the site, starting at the provided URL"""
        logger.debug("Got search URL %s", search_url)

        # load first page
        soup = self.get_page(search_url)

        # get data from first page
        entries = self.extract_data(soup)
        entries = self.entry_is_new_and_fits(entries, self.MODULE_NAME)
        logger.debug('Number of found entries: %d', len(entries))

        self.submit_to_entries(entries)

        return entries

    def submit_application(self, entry):
        contact_text_with_salutation = 'Guten Tag,\n\n' + self.contact_text

        # change the location of the driver on your machine
        self.driver.implicitly_wait(10)

        try:
            self.driver.get(entry['url'])
            # log in
            self.find_and_click('/html/body/app-root/div/div/div/div[1]/navigation-ui-header/div/header/div[2]/div[2]/div/nav/div/ul/li[1]/div/ul/li[1]/a')
            self.find_and_fill('/html/body/div[1]/div/div[1]/div/form[1]/div/div/div[1]/input', self.auto_submit_config['login_immowelt']['username'])
            self.find_and_fill('/html/body/div[1]/div/div[1]/div/form[1]/div/div/div[2]/div/input', self.auto_submit_config['login_immowelt']['password'])
            self.find_and_click('/html/body/div[1]/div/div[1]/div/form[1]/div/div/div[3]/input')
            logger.info('Login successful')
            try:
                self.try_solving_capthca(checkbox=True)
                self.find_and_click('/html/body/div[1]/div/div[1]/div/form[1]/div/div/div[3]/input')
            except CaptchaNotFound:
                pass
            # go back to the expose url
            self.driver.get(entry['url'])
            # click contact button
            self.find_and_click('/html/body/app-root/div/div/div/div[2]/main/app-expose/div[3]/div[3]/sd-container[1]/sd-row[9]/sd-col/app-offerer/sd-card/app-commercial-offerer/div[3]/sd-button/button')
            # fill out text field
            self.find_and_fill('/html/body/div[4]/div/div/div[2]/div/form/sd-form-field[3]/textarea', contact_text_with_salutation)
            # submit
            self.find_and_click('/html/body/div[4]/div/div/div[2]/div/form/sd-button/button')
        except NoSuchElementException as e:
            logger.debug("Unable to find HTML element")
            logger.debug("".join(traceback.TracebackException.from_exception(e).format()))
            raise ApplicationUnsuccesfulException