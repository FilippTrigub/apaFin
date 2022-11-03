"""Expose crawler for WgGesucht"""
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup
from selenium.common import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By

from flathunter.logging import logger
from flathunter.abstract_crawler import Crawler, ApplicationUnsuccesfulException
from flathunter.string_utils import remove_prefix


class CrawlWgGesucht(Crawler):
    """Implementation of Crawler interface for WgGesucht"""

    URL_PATTERN = re.compile(r'https://www\.wg-gesucht\.de')

    MODULE_NAME = 'wg_gesucht'

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.initialize_driver()

    def get_results(self, search_url, max_pages=None):
        entries = super().get_results(search_url, max_pages)
        entries = [entry for entry in entries if entry['id'] != 0]
        self.submit_to_entries(entries)

        return entries

    # pylint: disable=too-many-locals
    def extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []

        findings = soup.find_all(lambda e: e.has_attr('id') and e['id'].startswith('liste-'))
        existing_findings = [
            e for e in findings if e.has_attr('class') and not 'display-none' in e['class']
        ]

        base_url = 'https://www.wg-gesucht.de/'
        for row in existing_findings:
            title_row = row.find('h3', {"class": "truncate_title"})
            title = title_row.text.strip()
            url = base_url + remove_prefix(title_row.find('a')['href'], "/")
            image = re.match(r'background-image: url\((.*)\);',
                             row.find('div', {"class": "card_image"}).find('a')['style'])[1]
            detail_string = row.find("div", {"class": "col-xs-11"}).text.strip().split("|")
            details_array = list(map(lambda s: re.sub(' +', ' ',
                                                      re.sub(r'\W', ' ', s.strip())),
                                     detail_string))
            numbers_row = row.find("div", {"class": "middle"})
            price = numbers_row.find("div", {"class": "col-xs-3"}).text.strip()
            rooms_tmp = re.findall(r'\d Zimmer', details_array[0])
            rooms = rooms_tmp[0][:1] if rooms_tmp else 0
            dates = re.findall(r'\d{2}.\d{2}.\d{4}',
                               numbers_row.find("div", {"class": "text-center"}).text)
            if len(dates) == 0:
                logger.warning("No dates found - skipping")
                continue
            size = re.findall(r'\d{1,4}\sm²',
                              numbers_row.find("div", {"class": "text-right"}).text)
            if len(size) == 0:
                logger.warning("No size found - skipping")
                continue

            if len(dates) == 2:
                title = f"{title} vom {dates[0]} bis {dates[1]}"
            else:
                title = f"{title} ab dem {dates[0]}"

            details = {
                'id': int(url.split('.')[-2]),
                'image': image,
                'url': url,
                'title': title,
                'price': price,
                'size': size[0],
                'rooms': rooms,
                'address': url,
                'crawler': self.get_name()
            }
            if len(dates) == 2:
                details['from'] = dates[0]
                details['to'] = dates[1]
            elif len(dates) == 1:
                details['from'] = dates[0]

            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries

    def load_address(self, url):
        """Extract address from expose itself"""
        response = self.get_soup_from_url(url)
        try:
            address = ' '.join(response.find('div', {"class": "col-sm-4 mb10"})
                               .find("a", {"href": "#mapContainer"}).text.strip().split())
            return address
        except (TypeError, AttributeError):
            logger.debug("No address in response for URL: %s", url)
            return None

    def get_soup_from_url(
            self,
            url,
            driver=None,
            checkbox=None,
            afterlogin_string=None):
        """
        Creates a Soup object from the HTML at the provided URL

        Overwrites the method inherited from abstract_crawler. This is
        necessary as we need to reload the page once for all filters to
        be applied correctly on wg-gesucht.
        """
        self.rotate_user_agent()
        sess = requests.session()
        # First page load to set filters; response is discarded
        sess.get(url, headers=self.HEADERS)
        # Second page load
        resp = sess.get(url, headers=self.HEADERS)

        if resp.status_code not in (200, 405):
            logger.error("Got response (%i): %s", resp.status_code, resp.content)
        if self.config.use_proxy():
            return self.get_soup_with_proxy(url)
        if driver is not None:
            driver.get(url)
            if re.search("initGeetest", driver.page_source):
                self.resolve_geetest(driver)
            elif re.search("g-recaptcha", driver.page_source):
                self.resolve_recaptcha(driver, checkbox, afterlogin_string)
            return BeautifulSoup(driver.page_source, 'html.parser')
        return BeautifulSoup(resp.content, 'html.parser')

    def submit_application(self, entry):
        # todo does not work on 2nd entry
        # change the location of the driver on your machine
        self.driver.implicitly_wait(10)
        try:
            self.driver.get('https://www.wg-gesucht.de/nachricht-senden/' + entry['url'].split('/')[-1])
            self.click_away_conditions()

            # log in on first connect
            try:
                try:
                    self.find_and_click("//*[contains(text(), 'loggen')]")
                except ElementNotInteractableException:
                    self.find_and_click("//*[contains(text(), 'Login')]")
                self.find_and_fill(element='login_email_username',
                                   input_value=self.auto_submit_config['login_wggesucht']['username'], method=By.ID)
                self.find_and_fill(element='login_password',
                                   input_value=self.auto_submit_config['login_wggesucht']['password'], method=By.ID)

                self.find_and_click('login_submit', method=By.ID)
            except NoSuchElementException:
                pass

            se_button1 = self.driver.find_elements(By.ID, 'sicherheit_bestaetigung')
            timestamp = self.driver.find_elements(By.ID, 'time_stamp')
            if (len(se_button1) < 1 or len(timestamp) != 0):
                print("Already sent message to this offer...")
                return 0
            else:
                se_button1[0].click()

            # title element may vary in position
            for i in [3, 4, 5]:
                try:
                    title = self.driver.find_element(By.XPATH,
                                                     f'/html/body/div[3]/div[1]/div[3]/div[1]/div[1]/div[{i}]/div[1]/label/b')
                    break
                except NoSuchElementException:
                    pass
            title_words = title.text[:-1].split(' ')

            if 'Herr' in title_words and len(title_words) == title_words.index('Herr') + 2:
                greeting = f"Guten Tag Herr {title_words[title_words.index('Herr') + 1]},\n\n"
            elif 'Frau' in title_words and len(title_words) == title_words.index('Frau') + 2:
                greeting = f"Guten Tag Frau {title_words[title_words.index('Frau') + 1]},\n\n"
            else:
                greeting = "Guten Tag,\n\n"
            contact_text_with_salutation = greeting + self.contact_text

            self.find_and_fill(element='message_input', input_value=contact_text_with_salutation, method=By.ID)

            # add documents
            # self.find_and_click('//*[@id="messenger_form"]/div[1]/div[5]/button[2]')
            #
            # self.find_and_click('//*[@id="file_storage_wrapper"]/div[1]')
            #
            # self.find_and_click('//*[@id="attachments_modal"]/div/div/div[2]/div/div[2]/button')

            self.find_and_click("//button[@data-ng-click='submit()' or contains(.,'Nachricht senden')]")
        except NoSuchElementException as e:
            print("Unable to find HTML element")
            print("".join(traceback.TracebackException.from_exception(e).format()))
            raise ApplicationUnsuccesfulException

    def click_away_conditions(self):
        try:
            self.find_and_click('/html/body/div[2]/div[1]/div[2]/span[2]/a')
        except NoSuchElementException:
            pass
