import base64
import json
import os
import re
import urllib.parse
import zipfile

from io import BytesIO
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import InvalidSelectorException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import IEDriverManager, EdgeChromiumDriverManager


class Spydr:
    browsers = ('chrome', 'edge', 'firefox', 'ie', 'safari')
    by = By
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

    def __init__(self,
                 auth_username=None,
                 auth_password=None,
                 browser='chrome',
                 extension_root='./extensions',
                 headless=False,
                 screen_root='./screens',
                 timeout=30,
                 window_size='1280,720'):
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.browser = browser.lower()
        self.extension_root = extension_root
        self.headless = headless
        self.screen_root = screen_root
        self.window_size = window_size
        self.driver = self._get_webdriver()
        self.timeout = timeout

    def add_cookie(self, cookie):
        self.driver.add_cookie(cookie)

    def alert_accept(self, alert=None):
        if isinstance(alert, Alert):
            alert.accept()
        else:
            self.switch_to_alert().accept()

    def alert_dismiss(self, alert=None):
        if isinstance(alert, Alert):
            alert.dismiss()
        else:
            self.switch_to_alert().dismiss()

    def alert_sendkeys(self, keys_to_send, alert=None):
        if isinstance(alert, Alert):
            alert.send_keys(keys_to_send)
        else:
            self.switch_to_alert().send_keys(keys_to_send)

    def alert_text(self, alert=None):
        if isinstance(alert, Alert):
            alert.text
        else:
            self.switch_to_alert().text

    def back(self):
        self.driver.back()

    def blank(self):
        self.open('about:blank')

    def css_property(self, locator, name):
        return self.find_element(locator).value_of_css_property(name)

    def clear(self, locator):
        self.find_element(locator).clear()

    def click(self, locator):
        element = None

        if isinstance(locator, WebElement):
            element = locator
        else:
            element = self.find_element(locator)

        if element:
            self.wait_until(lambda _: self._is_element_clicked(element))

    def close(self):
        self.driver.close()

    @property
    def current_url(self):
        return self.driver.current_url

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def delete_cookie(self, name):
        self.driver.delete_cookie(name)

    @property
    def desired_capabilities(self):
        return self.driver.desired_capabilities

    def execute_async_script(self, script, *args):
        return self.driver.execute_async_script(script, *args)

    def execute_script(self, script, *args):
        return self.driver.execute_script(script, *args)

    def find_element(self, locator):
        if isinstance(locator, WebElement):
            return locator

        element = None
        how, what = self._parse_locator(locator)

        if how == self.hows['css']:
            matched = re.search(r'(.*):eq\((\d+)\)', what)
            if matched:
                new_what, nth = matched.group(1, 2)
                element = self.find_elements(f'css={new_what}')[int(nth)]

        element = element or self.driver.find_element(how, what)
        return element

    def find_elements(self, locator):
        how, what = self._parse_locator(locator)
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

    def is_element_located(self, locator, seconds=2):
        how, what = self._parse_locator(locator)

        self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda wd: wd.find_element(how, what))
        except (NoSuchElementException, NoSuchWindowException, StaleElementReferenceException, TimeoutException):
            return False
        finally:
            self.implicitly_wait = self.timeout

    def get_attribute(self, locator, name):
        return self.find_element(locator).get_attribute(name)

    def get_cookie(self, name):
        return self.driver.get_cookie(name)

    def get_cookies(self):
        return self.driver.get_cookies()

    def get_screenshot_as_base64(self):
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_as_file(self, filename):
        return self.driver.get_screenshot_as_file(self._abs_filename(filename))

    def get_screenshot_as_png(self):
        return self.driver.get_screenshot_as_png()

    def get_window_position(self, window_handle='current'):
        return self.driver.get_window_position(window_handle)

    def get_window_rect(self):
        return self.driver.get_window_rect()

    def get_window_size(self, window_handle='current'):
        return self.driver.get_window_size(window_handle)

    @property
    def implicitly_wait(self):
        return self.__implicitly_wait

    @implicitly_wait.setter
    def implicitly_wait(self, seconds):
        self.__implicitly_wait = seconds
        self.driver.implicitly_wait(seconds)

    def location(self, locator):
        return self.find_element(locator).location

    def maximize_window(self):
        if not self.headless:
            self.driver.maximize_window()

    def minimize_window(self):
        if not self.headless:
            self.driver.minimize_window()

    def open(self, url):
        self.driver.get(url)

    def open_with_auth(self, url, username=None, password=None):
        username = username or self.auth_username
        password = password or self.auth_password

        if username and password and self.browser != 'chrome':
            encoded_username = urllib.parse.quote(username)
            encoded_password = urllib.parse.quote(password)

            split_result = urllib.parse.urlsplit(url)
            split_result_with_auth = split_result._replace(
                netloc=f'{encoded_username}:{encoded_password}@{split_result.netloc}')

            url_with_auth = urllib.parse.urlunsplit(split_result_with_auth)

            self.open(url_with_auth)
        else:
            self.open(url)

    @property
    def page_load_timeout(self):
        return self.__page_load_timeout

    @page_load_timeout.setter
    def page_load_timeout(self, seconds):
        self.__page_load_timeout = seconds
        self.driver.set_page_load_timeout(seconds)

    @property
    def page_source(self):
        self.driver.page_source

    def quit(self):
        self.driver.quit()

    def refresh(self):
        self.driver.refresh()

    def rect(self, locator):
        return self.find_element(locator).rect

    def save_screenshot(self, filename):
        return self.driver.save_screenshot(self._abs_filename(filename))

    def select(self, option_locator):
        self.click(option_locator)

    def screenshot(self, locator, filename):
        return self.find_element(locator).screenshot(self._abs_filename(filename))

    def screenshot_as_base64(self, locator):
        return self.find_element(locator).screenshot_as_base64

    def screenshot_as_png(self, locator):
        return self.find_element(locator).screenshot_as_png

    def send_keys(self, locator, *keys):
        self.find_element(locator).send_keys(*keys)

    @property
    def script_timeout(self):
        return self.__script_timeout

    @script_timeout.setter
    def script_timeout(self, seconds):
        self.__script_timeout = seconds
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

    @property
    def switch_to_active_element(self):
        return self.driver.switch_to.active_element

    @property
    def switch_to_alert(self):
        return self.driver.switch_to.alert

    def switch_to_default_content(self):
        return self.driver.switch_to.default_content()

    def switch_to_frame(self, frame_reference):
        return self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        return self.driver.switch_to.parent_frame()

    def switch_to_window(self, window_name):
        return self.driver.switch_to.window(window_name)

    def tag_name(self, locator):
        return self.find_element(locator).tag_name

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, seconds):
        self.__timeout = seconds
        self.implicitly_wait = seconds
        self.page_load_timeout = seconds
        self.script_timeout = seconds

    def text(self, locator):
        return self.find_element(locator).text

    @property
    def title(self):
        return self.driver.title

    def wait_until(self, method):
        return self.wait(self.driver, self.timeout).until(method)

    def wait_until_alert_present(self):
        return self.wait_until(lambda _: self.ec.alert_is_present)

    def wait_until_attribute_contains(self, locator, attribute, value):
        return self.wait_until(lambda _: value in self.find_element(locator).get_attribute(attribute))

    def wait_until_frame_available_and_switch(self, frame_locator):
        return self.wait_until(lambda _: self.switch_to_frame(self.find_element(frame_locator)))

    def wait_until_elment_found_in_frame_and_switch(self, frame_locator, element_locator):
        self.switch_to_frame(self.find_element(frame_locator))
        return self.wait_until(lambda _: self.is_element_located(element_locator, seconds=self.timeout))

    def wait_until_enabled(self, locator):
        return self.wait_until(lambda _: self.is_enabled(locator))

    def wait_until_not(self, method):
        return self.wait(self.driver, self.timeout).until_not(method)

    def wait_until_not_visible(self, locator, seconds=2):
        self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda _: not self.find_element(locator))
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
            return True
        finally:
            self.implicitly_wait = self.timeout

    def wait_until_number_of_windows_to_be(self, number):
        return self.wait_until(self.ec.number_of_windows_to_be(number))

    def wait_until_selected(self, locator):
        return self.wait_until(lambda _: self.is_selected(locator))

    def wait_until_selection_to_be(self, locator, is_selected):
        return self.wait_until(lambda _: self.is_selected(locator) == is_selected)

    def wait_until_text_contains(self, locator, text):
        return self.wait_until(lambda _: text in self.find_element(locator).text)

    def wait_until_title_contains(self, title):
        return self.wait_until(self.ec.title_contains(title))

    def wait_until_url_contains(self, url):
        return self.wait_until(self.ec.url_contains(url))

    def wait_until_visible(self, locator):
        return self.wait_until(lambda _: self.is_displayed(locator))

    @property
    def window_handle(self):
        return self.driver.current_window_handle

    @property
    def window_handles(self):
        return self.driver.window_handles

    def _abs_filename(self, filename, suffix='.png', root=None):
        if not filename.lower().endswith(suffix):
            filename += suffix

        abspath = os.path.abspath(
            os.path.join(root or self.screen_root, filename))
        dirname = os.path.dirname(abspath)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return abspath

    def _auth_extension_as_base64(self, username, password):
        bytes_ = self._auth_extension_as_bytes(username, password)
        return base64.b64encode(bytes_).decode('utf-8')

    def _auth_extension_as_bytes(self, username, password):
        manifest = {
            "manifest_version": 2,
            "name": 'Spydr Authentication Extension',
            "version": '1.0.0',
            "permissions": ['<all_urls>', 'webRequest', 'webRequestBlocking'],
            "background": {
                "scripts": ['background.js']
            }
        }

        background = '''
            var username = '%s';
            var password = '%s';

            chrome.webRequest.onAuthRequired.addListener(
                function handler(details) {
                    if (username == null) {
                        return { cancel: true };
                    }

                    var authCredentials = { username: username, password: username };
                    // username = password = null;

                    return { authCredentials: authCredentials };
                },
                { urls: ['<all_urls>'] },
                ['blocking']
            );
        ''' % (username, password)

        buffer = BytesIO()
        zip = zipfile.ZipFile(buffer, 'w')
        zip.writestr('manifest.json', json.dumps(manifest))
        zip.writestr('background.js', background)
        zip.close()

        return buffer.getvalue()

    def _auth_extension_as_file(self, username, password, suffix='.crx'):
        bytes_ = self._auth_extension_as_bytes(username, password)
        filename = self._abs_filename(
            'spydr_auth', suffix=suffix, root=self.extension_root)

        f = open(filename, 'wb')
        f.write(bytes_)
        f.close()

        return filename

    def _chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('allow-running-insecure-content')
        options.add_argument('ignore-certificate-errors')
        options.add_argument('ignore-ssl-errors=yes')

        options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])

        if self.auth_username and self.auth_password:
            options.add_encoded_extension(self._auth_extension_as_base64(
                self.auth_username, self.auth_password))

        if self.headless:
            options.add_argument('headless')
            options.add_argument(f'window-size={self.window_size}')

        return options

    def _firefox_options(self):
        profile = webdriver.FirefoxProfile()
        profile.accept_untrusted_certs = True
        profile.assume_untrusted_cert_issuer = False
        # profile.set_preference(
        #     'network.automatic-ntlm-auth.trusted-uris', '.companyname.com')

        options = webdriver.FirefoxOptions()
        options.profile = profile

        if self.headless:
            options.add_argument('headless')

        return options

    def _get_webdriver(self):
        path = os.getcwd()

        if self.browser not in self.browsers:
            raise WebDriverException(f'Unsupported browser: {self.browser}')

        if self.browser == 'chrome':
            return webdriver.Chrome(
                executable_path=ChromeDriverManager(path=path).install(), options=self._chrome_options())
        elif self.browser == 'edge':
            return webdriver.Edge(EdgeChromiumDriverManager(path=path).install())
        elif self.browser == 'firefox':
            return webdriver.Firefox(
                executable_path=GeckoDriverManager(path=path).install(), options=self._firefox_options())
        elif self.browser == 'ie':
            return webdriver.Ie(executable_path=IEDriverManager(path=path).install(), options=self._ie_options())
        elif self.browser == 'safari':
            return webdriver.Safari()

    def _ie_options(self):
        options = webdriver.IeOptions()
        options.ensure_clean_session = True
        options.full_page_screenshot = True
        options.ignore_protected_mode_settings = True
        options.ignore_zoom_level = True
        options.native_events = False
        return options

    def _is_element_clicked(self, element):
        if not element.is_enabled():
            return False
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            return False

    def _parse_locator(self, locator):
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
                f'Failed to parse locator: {locator}')

        return how, what
