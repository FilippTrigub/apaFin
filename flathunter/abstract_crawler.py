"""Interface for webcrawlers. Crawler implementations should subclass this"""
import json
import os
import re
from time import sleep
import backoff
import requests
import selenium
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    ElementNotInteractableException, JavascriptException
from bs4 import BeautifulSoup
from random_user_agent.params import HardwareType, Popularity
from random_user_agent.user_agent import UserAgent
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import ChromeOptions

from flathunter import proxies
from flathunter.captcha.captcha_solver import CaptchaUnsolvableError
from flathunter.logging import logger


class Crawler:
    """Defines the Crawler interface"""

    AUTO_SUBMIT = False

    URL_PATTERN = None

    MODULE_NAME = None

    user_agent_rotator = UserAgent(popularity=[Popularity.COMMON.value],
                                   hardware_types=[HardwareType.COMPUTER.value])

    HEADERS = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': user_agent_rotator.get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;'
                  'q=0.9,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def __init__(self, config):
        self.config = config
        self.checkbox = None
        self.afterlogin_string = None
        self.auto_submit_config = config.get("auto_submit")
        self.AUTO_SUBMIT = self.auto_submit_config['enable']
        if self.AUTO_SUBMIT:
            self.contact_text = self.get_contact_text(self.auto_submit_config['contact_text_file'])

    def initialize_driver(self):
        if self.config.captcha_enabled():
            self.captcha_solver = self.config.get_captcha_solver()
            captcha_config = self.config.get('captcha')
            driver_arguments = captcha_config.get('driver_arguments', [])

            if captcha_config.get('checkbox', '') == "":
                self.checkbox = False
            else:
                self.checkbox = captcha_config.get('checkbox', '')
            if captcha_config.get('afterlogin_string', '') == "":
                self.afterlogin_string = ""
            else:
                self.afterlogin_string = captcha_config.get('afterlogin_string', '')
            if self.captcha_solver:
                self.driver = self.configure_driver(driver_arguments)

    def configure_driver(self, driver_arguments):
        """Configure Chrome WebDriver"""
        logger.info('Initializing Chrome WebDriver for crawler "%s"...', self.get_name())
        chrome_options = self.get_options(driver_arguments)
        if driver_arguments is not None:
            for driver_argument in driver_arguments:
                chrome_options.add_argument(driver_argument)

        driver = uc.Chrome(options=chrome_options)

        driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": ["https://api.geetest.com/get.*"]})
        driver.execute_cdp_cmd('Network.enable', {})

        return driver

    def rotate_user_agent(self):
        """Choose a new random user agent"""
        self.HEADERS['User-Agent'] = self.user_agent_rotator.get_random_user_agent()

    # pylint: disable=unused-argument
    def get_page(self, search_url, driver=None, page_no=None):
        """Applies a page number to a formatted search URL and fetches the exposes at that page"""
        return self.get_soup_from_url(search_url)

    @backoff.on_exception(wait_gen=backoff.constant,
                          exception=selenium.common.exceptions.TimeoutException,
                          max_tries=3)
    def get_soup_from_url(self, url, driver=None, checkbox=None, afterlogin_string=None):
        """Creates a Soup object from the HTML at the provided URL"""

        self.rotate_user_agent()
        resp = requests.get(url, headers=self.HEADERS)

        if resp.status_code not in (200, 405):
            logger.error("Got response (%i): %s", resp.status_code, resp.content)
        if self.config.use_proxy():
            return self.get_soup_with_proxy(url)
        if driver is not None:
            driver.get(url)
            if re.search("initGeetest", driver.page_source):
                try:
                    self.resolve_geetest(driver)
                except CaptchaUnsolvableError:
                    pass
            elif re.search("g-recaptcha", driver.page_source):
                try:
                    self.resolve_recaptcha(driver, checkbox, afterlogin_string)
                except CaptchaUnsolvableError:
                    pass
            return BeautifulSoup(driver.page_source, 'html.parser')
        return BeautifulSoup(resp.content, 'html.parser')

    def get_soup_with_proxy(self, url):
        """Will try proxies until it's possible to crawl and return a soup"""
        resolved = False
        resp = None

        # We will keep trying to fetch new proxies until one works
        while not resolved:
            proxies_list = proxies.get_proxies()
            for proxy in proxies_list:
                self.rotate_user_agent()

                try:
                    # Very low proxy read timeout, or it will get stuck on slow proxies
                    resp = requests.get(
                        url,
                        headers=self.HEADERS,
                        proxies={"http": proxy, "https": proxy},
                        timeout=(20, 0.1)
                    )

                    if resp.status_code != 200:
                        logger.error("Got response (%i): %s", resp.status_code, resp.content)
                    else:
                        resolved = True
                        break

                except requests.exceptions.ConnectionError:
                    logger.error("Connection failed for proxy %s. Trying new proxy...", proxy)
                except requests.exceptions.Timeout:
                    logger.error(
                        "Connection timed out for proxy %s. Trying new proxy...", proxy
                    )
                except requests.exceptions.RequestException:
                    logger.error("Some error occurred. Trying new proxy...")

        if not resp:
            raise Exception("An error occurred while fetching proxies or content")

        return BeautifulSoup(resp.content, 'html.parser')

    def extract_data(self, soup):
        """Should be implemented in subclass"""
        raise NotImplementedError

    # pylint: disable=unused-argument
    def get_results(self, search_url, max_pages=None):
        """Loads the exposes from the site, starting at the provided URL"""
        logger.debug("Got search URL %s", search_url)

        # load first page
        soup = self.get_page(search_url)

        # get data from first page
        entries = self.extract_data(soup)
        # apply crawler specific filter
        entries = self.entry_is_new_and_fits(entries, self.MODULE_NAME)
        logger.debug('Number of found entries: %d', len(entries))

        return entries

    def entry_is_new_and_fits(self, entries, module_name):
        """ Check whether apartment fits and is not present in json log. """
        filepath = os.path.join(os.getcwd(), module_name + '.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                already_contacted_entries = json.load(file)
        else:
            already_contacted_entries = {}

        filtered_entreis = []
        for entry in entries:
            if entry['id'] not in list(already_contacted_entries.keys()) and self.apartment_fits(entry):
                filtered_entreis.append(entry)
                already_contacted_entries.update({entry['id']: entry})

        # save contacted entries
        with open(filepath, 'w') as file:
            json.dump(already_contacted_entries, file)

        return filtered_entreis

    def submit_to_entries(self, entries):
        """ Submit to all available entries and log it. """
        if self.AUTO_SUBMIT:
            for entry in entries:
                try:
                    logger.info(f"Attempt automatic application for {entry['url']}")
                    self.submit_application(entry)
                    logger.info('Success')
                    entry.update({'applied': 'Yes'})
                except (Exception, ApplicationUnsuccesfulException):
                    logger.info('Failure')
                    entry.update({'applied': 'No'})

    def apartment_fits(self, entry):
        return True

    def submit_application(self, entry):
        raise NotImplementedError

    def crawl(self, url, max_pages=None):
        """Load as many exposes as possible from the provided URL"""
        if re.search(self.URL_PATTERN, url):
            try:
                return self.get_results(url, max_pages)
            except requests.exceptions.ConnectionError:
                logger.warning("Connection to %s failed. Retrying.", url.split('/')[2])
                return []
        return []

    def get_name(self):
        """Returns the name of this crawler"""
        return type(self).__name__

    def get_expose_details(self, expose):
        """Loads additional detalis for an expose. Should be implemented in the subclass"""
        return expose

    @backoff.on_exception(wait_gen=backoff.constant,
                          exception=CaptchaUnsolvableError,
                          max_tries=3)
    def resolve_geetest(self, driver):
        """Resolve GeeTest Captcha"""
        data = re.findall(
            "geetest_validate: obj.geetest_validate,\n.*?data: \"(.*)\"",
            driver.page_source
        )[0]
        result = re.findall(r"initGeetest\({(.*?)}", driver.page_source, re.DOTALL)

        geetest = re.findall("gt: \"(.*?)\"", result[0])[0]
        challenge = re.findall("challenge: \"(.*?)\"", result[0])[0]
        try:
            captcha_response = self.captcha_solver.solve_geetest(
                geetest,
                challenge,
                driver.current_url
            )
            script = (f'solvedCaptcha({{geetest_challenge: "{captcha_response.challenge}",'
                      f'geetest_seccode: "{captcha_response.sec_code}",'
                      f'geetest_validate: "{captcha_response.validate}",'
                      f'data: "{data}"}});')
            driver.execute_script(script)
            sleep(2)
        except CaptchaUnsolvableError:
            driver.refresh()
            raise

    @backoff.on_exception(wait_gen=backoff.constant,
                          exception=CaptchaUnsolvableError,
                          max_tries=3)
    def resolve_recaptcha(self, driver, checkbox: bool, afterlogin_string: str = ""):
        """Resolve Captcha"""
        iframe_present = self._wait_for_iframe(driver)
        if checkbox is False and afterlogin_string == "" and iframe_present:
            self.solve_defaut_recaptcha(driver)
        else:
            if checkbox:
                self._clickcaptcha(driver)
            else:
                self._wait_for_captcha_resolution(driver, afterlogin_string)

    def solve_defaut_recaptcha(self, driver, recaptchatype=1):
        google_site_key = driver \
            .find_element(By.CLASS_NAME, "g-recaptcha") \
            .get_attribute("data-sitekey")

        try:
            captcha_result = self.captcha_solver.solve_recaptcha(
                google_site_key,
                driver.current_url,
                recaptchatype=recaptchatype
            ).result

            driver.execute_script(
                f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_result}";'
            )

            # TODO: Below function call can be different depending on the websites
            #  implementation. It is responsible for sending the promise that we
            #  get from recaptcha_answer. For now, if it breaks, it is required to
            #  reverse engineer it by hand. Not sure if there is a way to automate it.
            try:
                driver.execute_script(f'solvedCaptcha("{captcha_result}")')
            except JavascriptException:
                driver.execute_async_script(
                    f"var payload = '{captcha_result}'; solvedCaptcha(payload);")

            self._wait_until_iframe_disappears(driver)
        except CaptchaUnsolvableError:
            driver.refresh()
            raise

    def _clickcaptcha(self, driver):
        driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
        self.find_and_click(element="recaptcha-checkbox-checkmark", method=By.CLASS_NAME)
        # todo if click was enough, app should pass here
        if not self.click_was_enough(driver):
            driver.switch_to.default_content()
            driver.refresh()
            raise ApplicationUnsuccesfulException
            # driver.switch_to.default_content()
            # # todo need to click on captcha to prolong its visibility and also find a way to submit result
            # try:
            #     iframe_present = self._wait_for_iframe(
            #         driver,
            #         element_selector="iframe[src^='https://www.google.com/recaptcha/api2/bframe?']")
            #     if iframe_present:
            #         self.solve_defaut_recaptcha(driver)
            #     WebDriverWait(driver, 30).until(
            #         EC.visibility_of_element_located((By.CLASS_NAME, "recaptcha-checkbox-checked"))
            #     )
            # except (selenium.common.exceptions.TimeoutException, selenium.common.exceptions.InvalidSelectorException):
            #     print("Solving ebay captcha not successful.")
            #     raise ApplicationUnsuccesfulException
        self._wait_for_captcha_resolution(driver)
        driver.switch_to.default_content()

    def click_was_enough(self, driver):
        try:
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "recaptcha-checkbox-checked")))
            return True
        except selenium.common.exceptions.TimeoutException:
            return False

    def _wait_for_captcha_resolution(self, driver, afterlogin_string=""):
        xpath_string = f"//*[contains(text(), '{afterlogin_string}')]"
        try:
            WebDriverWait(driver, 120) \
                .until(EC.visibility_of_element_located((By.XPATH, xpath_string)))
        except selenium.common.exceptions.TimeoutException:
            print("No Captcha solution found.")

    def _wait_for_iframe(self, driver: selenium.webdriver.Chrome, element_selector=None):
        """Wait for iFrame to appear"""
        iframe = None
        if not element_selector:
            element_selector = "iframe[src^='https://www.google.com/recaptcha/api2/anchor?']"
        while iframe is None:
            try:
                iframe = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, element_selector)))
                return iframe
            except (selenium.common.exceptions.TimeoutException, NoSuchElementException):
                logger.info("No iframe found, therefore no chaptcha verification necessary")
                return None

    def _wait_until_iframe_disappears(self, driver: selenium.webdriver.Chrome):
        """Wait for iFrame to disappear"""
        element_selectors = ["iframe[src^='https://www.google.com/recaptcha/api2/bframe?']",
                             "iframe[src^='https://www.google.com/recaptcha/api2/anchor?']"]
        element_selector = element_selectors.pop()
        try:
            WebDriverWait(driver, 10).until(EC.invisibility_of_element(
                (By.CSS_SELECTOR, element_selector)))
        except (selenium.common.exceptions.TimeoutException, NoSuchElementException):
            if len(element_selectors) == 0:
                logger.info("Element not found")

    def get_driver(self):
        captcha_config = self.config.get('captcha')
        driver_arguments = captcha_config.get('driver_arguments', [])
        return self.configure_driver(driver_arguments)

    def try_solving_capthca(self, checkbox=False):
        if re.search("initGeetest", self.driver.page_source):
            try:
                self.resolve_geetest(self.driver, checkbox)
            except CaptchaUnsolvableError:
                pass
        elif re.search("g-recaptcha", self.driver.page_source):
            self.resolve_recaptcha(self.driver, checkbox, self.afterlogin_string)
        else:
            raise CaptchaNotFound

    def get_options(self, driver_arguments):
        chrome_options = ChromeOptions()
        if driver_arguments is not None:
            for driver_argument in driver_arguments:
                chrome_options.add_argument(driver_argument)
        return chrome_options

    def find_and_click(self, element, method=By.XPATH):
        button = self.driver.find_element(method, element)
        if type(button) == list:
            button = button[0]
        try:
            button.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.driver.execute_script("arguments[0].click();", button)

    def find_and_fill(self, element, input_value, method=By.XPATH):
        text_area = self.driver.find_element(method, element)
        text_area.clear()
        text_area.send_keys(input_value)

    @staticmethod
    def get_contact_text(file_name):
        with open(file=os.path.join(os.getcwd(), file_name), encoding='utf-8') as file:
            return file.read()

    def click_away_conditions(self):
        NotImplementedError


class CaptchaNotFound(Exception):
    pass


class ApplicationUnsuccesfulException(Exception):
    pass
