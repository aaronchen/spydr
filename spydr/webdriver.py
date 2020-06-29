import os
import re

from os import path, makedirs
from selenium import webdriver
from selenium.common.exceptions import InvalidSelectorException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import IEDriverManager, EdgeChromiumDriverManager


class Spydr:
    browsers = ('chrome', 'edge', 'firefox', 'ie', 'safari')
    by = webdriver.common.by.By
    ec = EC
    hows = {
        'css': by.CSS_SELECTOR,
        'class': by.CLASS_NAME,
        'id': by.ID,
        'link_text': by.LINK_TEXT,
        'name': by.NAME,
        'partial_link_text': by.PARTIAL_LINK_TEXT,
        'tag_name': by.TAG_NAME,
        'xpath': by.XPATH
    }
    keys = webdriver.common.keys.Keys
    wait = webdriver.support.ui.WebDriverWait

    def __init__(self, browser='chrome', headless=False, screen_root='./screens', timeout=30, window_size='1280,720'):
        self.browser = browser
        self.headless = headless
        self.screen_root = screen_root
        self.timeout = timeout
        self.window_size = window_size
        self.driver = self.__get_webdriver()

        self.implicitly_wait(self.timeout)
        self.set_page_load_timeout(self.timeout)
        self.set_script_timeout(self.timeout)

    def add_cookie(self, cookie):
        self.driver.add_cookie(cookie)

    def back(self):
        self.driver.back()

    def blank(self):
        self.get('about:blank')

    def css_property(self, locator, name):
        return self.find_element(locator).value_of_css_property(name)

    def clear(self, locator):
        self.find_element(locator).clear()

    def click(self, locator):
        element = None

        if isinstance(locator, WebElement):
            element = locator
            self.wait_until(lambda wd: element.is_enabled())
        else:
            how, what = self.__parse_locator(locator)
            element = self.wait_until(
                self.ec.element_to_be_clickable((how, what)))

        if element:
            element.click()

    def close(self):
        self.driver.close()

    def current_url(self):
        return self.driver.current_url

    def current_window_handle(self):
        return self.driver.current_window_handle

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def delete_cookie(self, name):
        self.driver.delete_cookie(name)

    def desired_capabilities(self):
        return self.driver.desired_capabilities

    def execute_async_script(self, script, *args):
        return self.driver.execute_async_script(script, *args)

    def execute_script(self, script, *args):
        return self.driver.execute_script(script, *args)

    def find_element(self, locator):
        if isinstance(locator, WebElement):
            return locator

        how, what = self.__parse_locator(locator)
        element = self.driver.find_element(how, what)
        return element

    def find_elements(self, locator):
        how, what = self.__parse_locator(locator)
        elements = self.driver.find_elements(how, what)
        return elements

    def forward(self):
        self.driver.forward()

    def is_displayed(self, locator):
        return self.find_element(locator).is_displayed()

    def is_enabled(self, locator):
        return self.find_element(locator).is_enabled()

    def is_selected(self, locator):
        return self.find_element(locator).is_selected()

    def is_element_located(self, locator, seconds=1):
        how, what = self.__parse_locator(locator)

        self.implicitly_wait(seconds)

        try:
            return self.wait(self.driver, seconds).until(lambda wd: wd.find_element(how, what))
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
            return False
        finally:
            self.implicitly_wait(self.timeout)

    def get(self, url):
        self.driver.get(url)

    def get_attribute(self, locator, name):
        return self.find_element(locator).get_attribute(name)

    def get_cookie(self, name):
        return self.driver.get_cookie(name)

    def get_cookies(self):
        return self.driver.get_cookies()

    def get_screenshot_as_base64(self):
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_as_file(self, filename):
        return self.driver.get_screenshot_as_file(self.__abs_filename(filename))

    def get_screenshot_as_png(self):
        return self.driver.get_screenshot_as_png()

    def get_window_position(self, window_handle='current'):
        return self.driver.get_window_position(window_handle)

    def get_window_rect(self):
        return self.driver.get_window_rect()

    def get_window_size(self, window_handle='current'):
        return self.driver.get_window_size(window_handle)

    def implicitly_wait(self, seconds):
        self.driver.implicitly_wait(seconds)

    def location(self, locator):
        return self.find_element(locator).location

    def maximize_window(self):
        if not self.headless:
            self.driver.maximize_window()

    def minimize_window(self):
        if not self.headless:
            self.driver.minimize_window()

    def page_source(self):
        self.driver.page_source

    def quit(self):
        self.driver.quit()

    def refresh(self):
        self.driver.refresh()

    def rect(self, locator):
        return self.find_element(locator).rect

    def save_screenshot(self, filename):
        return self.driver.save_screenshot(self.__abs_filename(filename))

    def screenshot(self, locator, filename):
        return self.find_element(locator).screenshot(self.__abs_filename(filename))

    def screenshot_as_base64(self, locator):
        return self.find_element(locator).screenshot_as_base64

    def screenshot_as_png(self, locator):
        return self.find_element(locator).screenshot_as_png

    def send_keys(self, locator, *keys):
        self.find_element(locator).send_keys(*keys)

    def set_page_load_timeout(self, seconds):
        self.driver.set_page_load_timeout(seconds)

    def set_script_timeout(self, seconds):
        self.driver.set_script_timeout(seconds)

    def set_window_position(self, x, y, window_handle='current'):
        return self.driver.set_window_position(x, y, window_handle)

    def set_window_rect(self, x=None, y=None, width=None, height=None):
        return self.driver.set_window_rect(x, y, width, height)

    def set_window_size(self, width, height, window_handle='current'):
        return self.driver.set_window_size(width, height, window_handle)

    def size(self, locator):
        return self.find_element(locator).size

    def submit(self, locator):
        self.find_element(locator).submit()

    def switch_to_active_element(self):
        return self.driver.switch_to.active_element

    def switch_to_alert(self):
        return self.driver.switch_to.alert

    def switch_to_default_content(self):
        return self.driver.switch_to.switch_to_default_content()

    def switch_to_frame(self, frame_reference):
        return self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        return self.driver.switch_to.parent_frame()

    def switch_to_window(self, window_name):
        return self.driver.switch_to.window(window_name)

    def tag_name(self, locator):
        return self.find_element(locator).tag_name

    def text(self, locator):
        return self.find_element(locator).text

    def title(self):
        return self.driver.title

    def wait_until(self, method):
        return self.wait(self.driver, self.timeout).until(method)

    def wait_until_element_visible(self, locator):
        return self.wait_until(lambda wd: self.is_displayed(locator))

    def wait_until_element_not_visible(self, locator):
        if not isinstance(locator, WebElement):
            locator = self.__parse_locator(locator)
        return self.wait_until(self.ec.invisibility_of_element_located(locator))

    def wait_until_not(self, method):
        return self.wait(self.driver, self.timeout).until_not(method)

    def wait_until_title_contains(self, title):
        return self.wait_until(self.ec.title_contains(title))

    def wait_until_url_contains(self, url):
        return self.wait_until(self.ec.url_contains(url))

    def wait_until_attribute_contains(self, locator, attribute, css_class):
        element = self.find_element(locator)
        return self.wait_until(lambda wd: css_class in element.get_attribute(attribute))

    def window_handles(self):
        return self.driver.window_handles

    def __abs_filename(self, filename, suffix='.png'):
        if not filename.lower().endswith(suffix):
            filename += suffix

        abspath = path.abspath(path.join(self.screen_root, filename))
        dirname = path.dirname(abspath)

        if not path.exists(dirname):
            makedirs(dirname)

        return abspath

    def __chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])

        if self.headless:
            options.add_argument('headless')
            options.add_argument(
                'window-size={window_size}'.format(window_size=self.window_size))

        return options

    def __firefox_options(self):
        options = webdriver.FirefoxOptions()

        if self.headless:
            options.add_argument('headless')

        return options

    def __get_webdriver(self):
        if self.browser not in self.browsers:
            raise WebDriverException(
                'Unsupported browser: {browser}'.format(browser=self.browser))

        if self.browser == 'chrome':
            return webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=self.__chrome_options())
        elif self.browser == 'edge':
            return webdriver.Edge(EdgeChromiumDriverManager().install())
        elif self.browser == 'firefox':
            return webdriver.Firefox(
                executable_path=GeckoDriverManager().install(), options=self.__firefox_options())
        elif self.browser == 'ie':
            return webdriver.Ie(executable_path=IEDriverManager().install(), options=self.__ie_options())
        elif self.browser == 'safari':
            return webdriver.Safari()

    def __ie_options(self):
        options = webdriver.IeOptions()
        options.ensure_clean_session = True
        options.full_page_screenshot = True
        options.ignore_protected_mode_settings = True
        options.ignore_zoom_level = True
        options.native_events = False
        return options

    def __parse_locator(self, locator):
        how = what = None
        matched = re.search('^([A-Za-z]+)=(.+)', locator)

        if matched is None:
            what = locator
            if locator.startswith(('.', '#', '[')):
                how = self.hows['css']
            elif locator.startswith(('/', '(')):
                how = self.hows['xpath']
        else:
            somehow, what = matched.group(1, 2)
            if somehow in self.hows:
                how = self.hows[somehow]

        if how is None:
            raise InvalidSelectorException(
                'Failed to parse locator: {locator}'.format(locator=locator))

        return how, what
