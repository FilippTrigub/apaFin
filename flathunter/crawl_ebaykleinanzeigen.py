"""Expose crawler for Ebay Kleinanzeigen"""
import re
import datetime
import time
import traceback

from selenium.common import ElementNotInteractableException, NoSuchElementException, TimeoutException, \
    StaleElementReferenceException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By

from flathunter.logging import logger
from flathunter.abstract_crawler import Crawler, CaptchaNotFound
from selenium.webdriver.chrome.options import Options


class CrawlEbayKleinanzeigen(Crawler):
    """Implementation of Crawler interface for Ebay Kleinanzeigen"""

    MODULE_NAME = 'ebay'

    URL_PATTERN = re.compile(r'https://www\.ebay-kleinanzeigen\.de')
    MONTHS = {
        "Januar": "01",
        "Februar": "02",
        "März": "03",
        "April": "04",
        "Mai": "05",
        "Juni": "06",
        "Juli": "07",
        "August": "08",
        "September": "09",
        "Oktober": "10",
        "November": "11",
        "Dezember": "12"
    }

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.initialize_driver()
        self.checkbox = True

    def get_results(self, search_url, max_pages=None):
        entries = super().get_results(search_url, max_pages)
        self.submit_to_entries(entries)

        return entries

    def get_page(self, search_url, driver=None, page_no=None):
        """Applies a page number to a formatted search URL and fetches the exposes at that page"""
        return self.get_soup_from_url(search_url)

    def get_expose_details(self, expose):
        soup = self.get_page(expose['url'])
        for detail in soup.find_all('li', {"class": "addetailslist--detail"}):
            if re.match(r'Verfügbar ab', detail.text):
                date_string = re.match(r'(\w+) (\d{4})', detail.text)
                if date_string is not None:
                    expose['from'] = "01." + self.MONTHS[date_string[1]] + "." + date_string[2]
        if 'from' not in expose:
            expose['from'] = datetime.datetime.now().strftime('%02d.%02m.%Y')
        return expose

    # pylint: disable=too-many-locals
    def extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []
        soup = soup.find(id="srchrslt-adtable")

        try:
            title_elements = soup.find_all(lambda e: e.has_attr('class')
                                                     and 'ellipsis' in e['class'])
        except AttributeError:
            return entries

        expose_ids = soup.find_all("article", class_="aditem")

        for idx, title_el in enumerate(title_elements):
            try:
                price = expose_ids[idx].find(class_="aditem-main--middle--price-shipping--price").text.strip()
                tags = expose_ids[idx].find_all(class_="simpletag tag-small")
                address = expose_ids[idx].find("div", {"class": "aditem-main--top--left"})
                image_element = expose_ids[idx].find("div", {"class": "galleryimage-element"})
            except AttributeError as error:
                logger.warning("Unable to process eBay expose: %s", str(error))
                continue

            if image_element is not None:
                image = image_element["data-imgsrc"]
            else:
                image = None

            address = address.text.strip()
            address = address.replace('\n', ' ').replace('\r', '')
            address = " ".join(address.split())

            try:
                rooms = re.match(r'(\d+)', tags[1].text)[1]
            except (IndexError, TypeError):
                rooms = ""
            try:
                size = tags[0].text
            except (IndexError, TypeError):
                size = ""
            details = {
                'id': int(expose_ids[idx].get("data-adid")),
                'image': image,
                'url': ("https://www.ebay-kleinanzeigen.de" + title_el.get("href")),
                'title': title_el.text.strip(),
                'price': price,
                'size': size,
                'rooms': rooms,
                'address': address,
                'crawler': self.get_name()
            }
            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries

    def load_address(self, url):
        """Extract address from expose itself"""
        expose_soup = self.get_page(url)
        try:
            street_raw = expose_soup.find(id="street-address").text
        except AttributeError:
            street_raw = ""
        try:
            address_raw = expose_soup.find(id="viewad-locality").text
        except AttributeError:
            address_raw = ""
        address = address_raw.strip().replace("\n", "") + " " + street_raw.strip()

        return address

    def apartment_fits(self, entry):
        accaptable_quartiers = ['Prenzlauer Berg', 'Friedrichshain', 'Mitte', 'Kreuzberg', 'Charlottenburg',
                                'Tempelhof', 'Neukölln']
        forbidden_keywords = ['Zwischenmiete', 'Untermiete', 'befristet', 'zeitweise']
        if any([quartier.lower() in entry['address'].lower() for quartier in accaptable_quartiers]) \
                and not any([no_go.lower() in entry['title'].lower() for no_go in forbidden_keywords]):
            return True
        else:
            return False

    def get_options(self, driver_arguments):
        chrome_options = Options()
        if driver_arguments is not None:
            for driver_argument in driver_arguments:
                chrome_options.add_argument(driver_argument)
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation']) todo
        return chrome_options

    def submit_application(self, entry):
        contact_text_with_salutation = 'Guten Tag,\n\n' + self.contact_text

        # change the location of the driver on your machine
        self.driver.implicitly_wait(10)

        try:
            self.driver.get(entry['url'])
            self.click_away_conditions()
            # log in only required at beginning
            try:
                # log in button
                self.find_and_click(element="viewad-contact-button-login-modal", method=By.ID)

                # Captchas might appear here.
                self.click_away_conditions()
                try:
                    # self.try_solving_capthca(checkbox=False)
                    self.try_solving_capthca(checkbox=self.checkbox)
                except (TimeoutException, CaptchaNotFound):
                    pass

                # username and password, then click log in
                self.find_and_fill(element='/html/body/div[1]/div/div[3]/div[1]/form/div[1]/div/div/input', input_value=self.auto_submit_config['login_ebay']['username'])
                self.find_and_fill(element='/html/body/div[1]/div/div[3]/div[1]/form/div[2]/div/div/input', input_value=self.auto_submit_config['login_ebay']['password'])
                self.find_and_click('/html/body/div[1]/div/div[3]/div[1]/form/div[4]/div/div/button')
            except NoSuchElementException:
                pass

            self.find_and_fill(element='#viewad-contact-form > fieldset > div:nth-child(1) > div > textarea', method=By.CSS_SELECTOR, input_value=contact_text_with_salutation)

            self.find_and_click(element="#viewad-contact-form > fieldset > div.formgroup.formgroup--btn-submit-right > button", method=By.CSS_SELECTOR)

        except NoSuchElementException as e:
            print("Unable to find HTML element")
            print("".join(traceback.TracebackException.from_exception(e).format()))

    def click_away_conditions(self):
        # click away conditions
        try:
            self.find_and_click(element='gdpr-banner-accept', method=By.ID)
            self.find_and_click(element='#gdpr-banner-accept', method=By.CSS_SELECTOR)
            self.find_and_click(element='/html/body/div[2]/div/div/div/div/div[3]/button[2]')
        except (NoSuchElementException, StaleElementReferenceException):
            pass
