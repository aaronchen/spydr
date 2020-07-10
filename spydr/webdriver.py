import base64
import json
import os
import re
import urllib.parse
import zipfile

from io import BytesIO
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import InvalidSelectorException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchFrameException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from time import strftime, localtime
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import IEDriverManager, EdgeChromiumDriverManager


class Spydr:
    """Spydr Webdriver

    Keyword Arguments:
        auth_username (str): Username for HTTP Basic/Digest Auth. Defaults to None.
        auth_password (str): Password for HTTP Basic/Digest Auth. Defaults to None.
        browser (str): Browser to drive.  Defaults to 'chrome'.
            Supported browsers: 'chrome', 'edge', 'firefox', 'ie', 'safari'.
        extension_root (str): The directory of Extensions. Defaults to './extensions'.
        headless (bool): Headless mode. Defaults to False.
        log_indentation (int): Indentation for log messages. Defaults to 2.
        log_prefix (str): Prefix for log messages. Defaults to '- '.
        screen_root (str): The directory of saved screenshots. Defaults to './screens'.
        timeout (int): Timeout for implicitly_wait, page_load_timeout, and script_timeout. Defaults to 30.
        verbose (bool): Turn on/off verbose mode. Defaults to True.
        window_size (str): The size of the window when headless.  Defaults to '1280,720'.

    Raises:
        NoSuchElementException: Raise an error when no element is found
        WebDriverException: Raise an error when Spydr encounters an error
        InvalidSelectorException: Raise an error when locator is invalid

    Returns:
        Spydr: An instance of Spydr Webdriver
    """

    browsers = ('chrome', 'edge', 'firefox', 'ie', 'safari')
    """Supported Browsers"""

    by = By
    """Set of supported locator strategies"""

    ec = expected_conditions
    """Pre-defined Expected Conditions"""

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
    """Set of How locators"""

    keys = Keys
    """Pre-defined keys codes"""

    wait = WebDriverWait
    """WebDriverWait"""

    def __init__(self,
                 auth_username=None,
                 auth_password=None,
                 browser='chrome',
                 extension_root='./extensions',
                 headless=False,
                 log_indentation=2,
                 log_prefix='- ',
                 screen_root='./screens',
                 timeout=30,
                 verbose=True,
                 window_size='1280,720'):
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.browser = browser.lower()
        self.extension_root = extension_root
        self.headless = headless
        self.log_indentation = log_indentation
        self.log_prefix = log_prefix
        self.screen_root = screen_root
        self.verbose = verbose
        self.window_size = window_size
        self.driver = self._get_webdriver()
        self.timeout = timeout

    def actions(self):
        """Initialize an ActionChains.

        Returns:
            ActionChains: An instance of ActionChains
        """
        return ActionChains(self.driver)

    def add_cookie(self, cookie):
        """Add a cookie to your current session.

        Args:
            cookie (dict): A dictionary object.
                Required keys are "name" and "value".
                Optional keys are "path", "domain", "secure", and "expiry".

        Usage:
            spydr.add_cookie({'name': 'foo', 'value': 'bar'})
        """
        self.driver.add_cookie(cookie)

    def alert_accept(self, alert=None):
        """Accept the alert available.

        Keyword Arguments:
            alert (Alert, optional): Alert instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.accept()
        else:
            self.switch_to_alert().accept()

    def alert_dismiss(self, alert=None):
        """Dismiss the alert available.

        Keyword Arguments:
            alert (Alert, optional): Alert instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.dismiss()
        else:
            self.switch_to_alert().dismiss()

    def alert_sendkeys(self, keys_to_send, alert=None):
        """Send keys to the alert.

        Args:
            keys_to_send (str): Text to send

        Keyword Arguments:
            alert (Alert, optional): Alert instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.send_keys(keys_to_send)
        else:
            self.switch_to_alert().send_keys(keys_to_send)

    def alert_text(self, alert=None):
        """Get the text of the alert.

        Keyword Arguments:
            alert (Alert, optional): Alert Instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.text
        else:
            self.switch_to_alert().text

    def back(self):
        """Goes one step backward in the browser history"""
        self.driver.back()

    def blank(self):
        """Open a blank page."""
        self.open('about:blank')

    def blur(self, locator):
        """Trigger blur event on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.execute_script('arguments[0].blur();', self.find_element(locator))

    def css_property(self, locator, name):
        """The value of CSS property.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            name (str): CSS property name

        Returns:
            str: CSS property value
        """
        return self.find_element(locator).value_of_css_property(name)

    def clear(self, locator):
        """Clear the text of a text input element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).clear()

    def click(self, locator):
        """Click the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.wait_until(lambda _: self._is_element_clicked(locator))

    def click_with_offset(self, locator, x_offset=1, y_offset=1):
        """Click the element from x and y offsets.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            x_offset (int, optional): X offset from the left of the element. Defaults to 1.
            y_offset (int, optional): Y offset from the top of the element. Defaults to 1.
        """
        element = self.find_element(locator)
        self.wait_until_enabled(element)
        self.actions().move_to_element_with_offset(
            element, x_offset, y_offset).click().perform()

    def close(self):
        """Close the window."""
        self.driver.close()

    @property
    def current_url(self):
        """Get the URL of the current page.

        Returns:
            str: URL of the page
        """
        return self.driver.current_url

    def delete_all_cookies(self):
        """Delete all cookies in the scope of the session."""
        self.driver.delete_all_cookies()

    def delete_cookie(self, name):
        """Delete a cookie with the given name.

        Args:
            name (str): Name of the cookie
        """
        self.driver.delete_cookie(name)

    @property
    def desired_capabilities(self):
        """Get driver's current desired capabilities.

        Returns:
            dict: A dictionary object of the current capabilities
        """
        return self.driver.desired_capabilities

    def double_click(self, locator):
        """Double-click the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        element = self.find_element(locator)
        self.actions().move_to_element(element).double_click().perform()

    def double_click_with_offset(self, locator, x_offset=1, y_offset=1):
        """Double-click the element from x and y offsets.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            x_offset (int): X offset from the left of the element. Defaults to 1.
            y_offset (int): Y offset from the top of the element. Defaults to 1.
        """
        element = self.find_element(locator)
        self.actions().move_to_element_with_offset(
            element, x_offset, y_offset).double_click().perform()

    def drag_and_drop(self, source_locator, target_locator):
        """Hold down the left mouse button on the source element,
        then move to the target element and releases the mouse button.

        Args:
            source_locator (str/WebElement): The element to mouse down
            target_locator (str/WebElement): The element to mouse up
        """
        source_element = self.find_element(source_locator)
        target_element = self.find_element(target_locator)
        self.actions().drag_and_drop(source_element, target_element()).perform()

    def drag_and_drop_by_offset(self, source_locator, x_offset, y_offset):
        """Hold down the left mouse button on the source element, 
        then move to the target offset and releases the mouse button.

        Args:
            source_locator (str/WebElement): The element to mouse down

        Keyword Arguments:
            x_offset (int): X offset to move to
            y_offset (int): Y offset to move to
        """
        source_element = self.find_element(source_locator)
        self.actions().drag_and_drop_by_offset(
            source_element, x_offset, y_offset).perform()

    def execute_async_script(self, script, *args):
        """Asynchronously execute JavaScript in the current window or frame.

        Args:
            script (str): JavaScript to execute
            *args: Any applicable arguments for JavaScript

        Returns:
            Any applicable return from JavaScript
        """
        return self.driver.execute_async_script(script, *args)

    def execute_script(self, script, *args):
        """Synchronously execute JavaScript in the current window or frame.

        Args:
            script (str): JavaScript to execute
            *args: Any applicable arguments for JavaScript

        Returns:
            Any applicable return from JavaScript
        """
        return self.driver.execute_script(script, *args)

    def find_element(self, locator):
        """Find the element by the given locator.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Raises:
            NoSuchElementException: Raise an error when no element found

        Returns:
            WebElement: The element found
        """
        if isinstance(locator, WebElement):
            return locator

        element = None
        how, what = self._parse_locator(locator)

        if how == self.hows['css']:
            matched = re.search(r'(.*):eq\((\d+)\)', what)
            if matched:
                new_what, nth = matched.group(1, 2)
                try:
                    element = self.find_elements(f'css={new_what}')[int(nth)]
                except IndexError:
                    raise NoSuchElementException(
                        f'{locator} does not have {nth} element')

        element = element or self.driver.find_element(how, what)
        return element

    def find_elements(self, locator):
        """Find all elements by the given locator.

        Args:
            locator (str): The locator to identify the element

        Returns:
            list[WebElement]: All elements found
        """
        how, what = self._parse_locator(locator)
        elements = self.driver.find_elements(how, what)
        return elements

    def focus(self, locator):
        """Trigger focus event on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.execute_script(
            'arguments[0].focus();', self.find_element(locator))

    def forward(self):
        """Goes one step forward in the browser history."""
        self.driver.forward()

    def fullscreen_window(self):
        """Invokes the window manager-specific 'full screen' operation."""
        self.driver.fullscreen_window()

    def get_attribute(self, locator, name):
        """Get the given attribute or property of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            name (str): Attribute name

        Returns:
            bool/str/None: The attribute value
        """
        return self.find_element(locator).get_attribute(name)

    def get_cookie(self, name):
        """Get the cookie by name.

        Args:
            name (str): The name of the cookie

        Returns:
            dict/None: Return the cookie or None if not found.
        """
        return self.driver.get_cookie(name)

    def get_cookies(self):
        """Get the cookies visible in the current session.

        Returns:
            list[dict]: Return cookies in a set of dictionaries
        """
        return self.driver.get_cookies()

    def get_screenshot_as_base64(self):
        """Get a screenshot of the current window as a base64 encoded string.

        Returns:
            str: Base64 encoded string of the screenshot
        """
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_as_file(self, filename):
        """Save a screenshot of the current window to filename (PNG).

        Default directory for saved screenshots is defined in: screen_root.

        Args:
            filename (str): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        return self.driver.get_screenshot_as_file(self._abs_filename(filename))

    def get_screenshot_as_png(self):
        """Get a screenshot of the current window as a binary data.

        Returns:
            bytes: Binary data of the screenshot
        """
        return self.driver.get_screenshot_as_png()

    def get_window_position(self, window_handle='current'):
        """Get the x and y position of the given window.

        Keyword Arguments:
            window_handle (str, optional): The handle of the window. Defaults to 'current'.

        Returns:
            dict: The position of the window as dict: {'x': 0, 'y': 0}
        """
        return self.driver.get_window_position(window_handle)

    def get_window_rect(self):
        """Get the x, y, height, and width of the current window.

        Returns:
           dict: The position, height, and width as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.get_window_rect()

    def get_window_size(self, window_handle='current'):
        """Get the width and height of the given window.

        Keyword Arguments:
            window_handle (str, optional): The handle of the window. Defaults to 'current'.

        Returns:
            dict: The height and width of the window as dict: {'width': 100, 'height': 100}
        """
        return self.driver.get_window_size(window_handle)

    def has_attribute(self, locator, attribute):
        """Check if the element has the given attribute.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name

        Returns:
            bool: Whether the attribute exists
        """
        return self.execute_script(
            'return arguments[0].hasAttribute(arguments[1]);', self.find_element(locator), attribute)

    def hide(self, locator):
        """Hide the element."""
        self.execute_script(
            'arguments[0].style.display = "none";', self.find_element(locator))

    def highlight(self, locator, hex_color='#ff3'):
        """Highlight the element with the given color.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            hex_color (str, optional): Hex color. Defaults to '#ff3'.
        """
        self.execute_script(
            'arguments[0].style.backgroundColor = `${arguments[1]}`;', self.find_element(locator), hex_color)

    @property
    def implicitly_wait(self):
        """Timeout for implicitly wait.

        Returns:
            int: The timeout of implicitly wait
        """
        return self.__implicitly_wait

    @implicitly_wait.setter
    def implicitly_wait(self, seconds):
        self.__implicitly_wait = seconds
        self.driver.implicitly_wait(seconds)

    def is_displayed(self, locator):
        """Check if the element is visible.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is visible
        """
        return self.find_element(locator).is_displayed()

    def is_enabled(self, locator):
        """Check if the element is enabled.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is enabled
        """
        return self.find_element(locator).is_enabled()

    def is_selected(self, locator):
        """Check if the element is selected.

        Can be used to check if a checkbox or radio button is selected.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is selected
        """
        return self.find_element(locator).is_selected()

    def is_element_located(self, locator, seconds=2):
        """Check if the element can be located in the given seconds.

        Args:
            locator (str): The locator to identify the element

        Keyword Arguments:
            seconds (int, optional): Seconds to wait until giving up. Defaults to 2.

        Returns:
            False/WebElement: Return False if not located.  Return WebElement if located.
        """
        how, what = self._parse_locator(locator)

        self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda wd: wd.find_element(how, what))
        except (NoSuchElementException, NoSuchWindowException, StaleElementReferenceException, TimeoutException):
            return False
        finally:
            self.implicitly_wait = self.timeout

    def location(self, locator):
        """The location of the element in the renderable canvas.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The location of the element as dict: {'x': 0, 'y': 0}
        """
        return self.find_element(locator).location

    def log(self, message, indentation=None):
        """Log message.

        Args:
            message (str): Message to log

        Keyword Arguments:
            indentation (int, optional): Indentation for log message. Defaults to None.
        """
        if not self.verbose:
            return

        indentation = indentation or self.log_indentation
        print(f'{" " * indentation}{self.log_prefix}{message}')

    def maximize_window(self):
        """Maximize the current window."""
        if not self.headless:
            self.driver.maximize_window()

    def maximize_to_screen(self):
        """Maximize the current window to match the screen size."""
        size = self.execute_script(
            'return { width: window.screen.width, height: window.screen.height };')
        self.set_window_position(0, 0)
        self.set_window_size(size['width'], size['height'])

    def minimize_window(self):
        """Minimize the current window."""
        if not self.headless:
            self.driver.minimize_window()

    def move_by_offset(self, x_offset, y_offset):
        """Moving the mouse to an offset from current mouse position.

        Keyword Arguments:
            x_offset (int): X offset
            y_offset (int): Y offset
        """
        self.actions().move_by_offset(x_offset, y_offset).perform()

    def move_to_element(self, locator):
        """Moving the mouse to the middle of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        element = self.find_element(locator)
        self.actions().move_to_element(element).perform()

    def move_to_element_with_offset(self, locator, x_offset=1, y_offset=1):
        """Move the mouse by an offset of the specified element.
        Offsets are relative to the top-left corner of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            x_offset (int, optional): X offset. Defaults to 1.
            y_offset (int, optional): Y offset. Defaults to 1.
        """
        element = self.find_element(locator)
        self.actions().move_to_element_with_offset(
            element, x_offset, y_offset).perform()

    def new_tab(self):
        """Open a new tab.

        Returns:
            str: Window handle of the new tab
        """
        self.execute_script('window.open();')
        return self.window_handles[-1]

    def new_window(self, name):
        """Open a new window.

        Args:
            name (str): Name of the window

        Returns:
            str: Window handle of the new window
        """
        self.execute_script('''
            var w = Math.max(
                document.documentElement.clientWidth, window.innerWidth || 0
            );
            var h = Math.max(
                document.documentElement.clientHeight, window.innerHeight || 0
            );
            window.open("about:blank", arguments[0], `width=${w},height=${h}`);
        ''', name)
        return self.window_handles[-1]

    def open(self, url):
        """Load the web page by its given URL.

        Args:
            url (str): URL of the web page
        """
        self.driver.get(url)

    def open_with_auth(self, url, username=None, password=None):
        """Load the web page by adding username and password to the URL

        Args:
            url (str): URL of the web page

        Keyword Arguments:
            username (str, optional): Username. Defaults to auth_username or None.
            password (str, optional): Password. Defaults to auth_password or None.
        """
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
        """Timeout for page load

        Returns:
            int: Page load timeout
        """
        return self.__page_load_timeout

    @page_load_timeout.setter
    def page_load_timeout(self, seconds):
        self.__page_load_timeout = seconds
        self.driver.set_page_load_timeout(seconds)

    @property
    def page_source(self):
        """Get the source of the current page.

        Returns:
            str: The source of the current page
        """
        return self.driver.page_source

    def quit(self):
        """Quit the Spydr webdriver."""
        self.driver.quit()

    def refresh(self):
        """Refresh the current page."""
        self.driver.refresh()

    def rect(self, locator):
        """Get the size and location of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The size and location of the element as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.find_element(locator).rect

    def remove_attribute(self, locator, attribute):
        """Remove the given attribute from the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
        """
        self.execute_script('''
            var element = arguments[0];
            var attributeName = arguments[1];
            if (element.hasAttribute(attributeName)) {
                element.removeAttribute(attributeName);
            }
        ''', self.find_element(locator), attribute)

    def right_click(self, locator):
        """Right-click on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        element = self.find_element(locator)
        self.actions().move_to_element(element).context_click().perform()

    def right_click_with_offset(self, locator, x_offset=1, y_offset=1):
        """Right-click on the element with x and y offsets

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            x_offset (int, optional): X offset from the left of the element. Defaults to 1.
            y_offset (int, optional): Y offset from the top of the element. Defaults to 1.
        """
        element = self.find_element(locator)

        self.actions().move_to_element_with_offset(
            element, x_offset, y_offset).context_click().perform()

    def save_screenshot(self, filename):
        """Save a screenshot of the current window to filename (PNG).

        Default directory for saved screenshots is defined in: screen_root.

        Args:
            filename (str): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        return self.driver.save_screenshot(self._abs_filename(filename))

    def screenshot(self, locator, filename):
        """Save a screenshot of the current element to the filename (PNG).

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            filename ([type]): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        return self.find_element(locator).screenshot(self._abs_filename(filename))

    def screenshot_as_base64(self, locator):
        """Get the screenshot of the current element as a Base64 encoded string

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: Base64 encoded string of the screenshot
        """
        return self.find_element(locator).screenshot_as_base64

    def screenshot_as_png(self, locator):
        """Get the screenshot of the current element as a binary data.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bytes: Binary data of the screenshot
        """
        return self.find_element(locator).screenshot_as_png

    @property
    def script_timeout(self):
        """Timeout for script.

        Returns:
            int: Script timeout
        """
        return self.__script_timeout

    @script_timeout.setter
    def script_timeout(self, seconds):
        self.__script_timeout = seconds
        self.driver.set_script_timeout(seconds)

    def scroll_into_view(self, locator, align_to=True):
        """Scroll the element's parent to be visible.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            align_to (bool, optional): When True, align the top of the element to the top.
                When False, align the bottom of the element to the bottom. Defaults to True.
        """
        self.execute_script(
            'arguments[0].scrollIntoView(arguments[1]);', self.find_element(locator), align_to)

    def select(self, option_locator):
        """Select the given option in the drop-down menu.

        Args:
            option_locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.click(option_locator)

    def send_keys(self, locator, *keys):
        """Simulate typing into the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            *keys: Any combinations of strings
        """
        self.find_element(locator).send_keys(*keys)

    def set_attribute(self, locator, attribute, value):
        """Set the given value to the attribute of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
            value (str): Attribute name
        """
        self.execute_script('''
            var element = arguments[0];
            var attribute = arguments[1];
            var value = arguments[2];
            element.setAttribute(attribute, value);
        ''', self.find_element(locator), attribute, value)

    def set_window_position(self, x, y, window_handle='current'):
        """Set the x and y position of the current window

        Args:
            x (int): x-coordinate in pixels
            y (int): y-coordinate in pixels

        Keyword Arguments:
            window_handle (str, optional): Window handle. Defaults to 'current'.

        Returns:
            dict: Window rect as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.set_window_position(x, y, window_handle)

    def set_window_rect(self, x=None, y=None, width=None, height=None):
        """Set the x, y, width, and height of the current window.

        Keyword Arguments:
            x (int, optional): x-coordinate in pixels. Defaults to None.
            y (int, optional): y-coordinate in pixels. Defaults to None.
            width (int, optional): Window width in pixels. Defaults to None.
            height (int, optional): Window height in pixels. Defaults to None.

        Returns:
            dict: Window rect as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.set_window_rect(x, y, width, height)

    def set_window_size(self, width, height, window_handle='current'):
        """Set the width and height of the current window.

        Args:
            width (int, optional): Window width in pixels. Defaults to None.
            height (int, optional): Window height in pixels. Defaults to None.

        Keyword Arguments:
            window_handle (str, optional): Window handle. Defaults to 'current'.

        Returns:
            dict: Window rect as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.set_window_size(width, height, window_handle)

    def show(self, locator):
        """Show the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.execute_script(
            'arguments[0].style.display = "";', self.find_element(locator))

    def size(self, locator):
        """The size of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The size of the element as dict: {'width': 100, 'height': 100}
        """
        return self.find_element(locator).size

    def submit(self, locator):
        """Submit a form.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).submit()

    @property
    def switch_to_active_element(self):
        """Switch to active element.

        Returns:
            WebElement: Active Element
        """
        return self.driver.switch_to.active_element

    @property
    def switch_to_alert(self):
        """Switch to alert.

        Returns:
            Alert: Alert
        """
        return self.driver.switch_to.alert

    def switch_to_default_content(self):
        """Switch to default content."""
        self.driver.switch_to.default_content()

    def switch_to_frame(self, frame_locator):
        """Switch to frame.

        Args:
            frame_locator (str/WebElement): The locator to identify the frame or WebElement
        """
        self.driver.switch_to.frame(self.find_element(frame_locator))

    def switch_to_frame_and_wait_until_elment_located_in_frame(self, frame_locator, element_locator):
        """Switch to the given frame and wait until the element is located within the frame.

        Args:
            frame_locator (str/WebElement): The locator to identify the frame or WebElement
            element_locator (str): The locator to identify the element

        Returns:
            False/WebElement: Return False if not located.  Return WebElement if located.
        """
        self.wait_until_frame_available_and_switch(frame_locator)
        return self.wait_until(lambda _: self.is_element_located(element_locator, seconds=self.timeout))

    def switch_to_last_window_handle(self):
        """Switch to the last opened tab or window."""
        self.switch_to_window(self.window_handles[-1])

    def switch_to_parent_frame(self):
        """Switch to parent frame."""
        self.driver.switch_to.parent_frame()

    def switch_to_window(self, window_name):
        """Switch to window.

        Args:
            window_name (str): Window name
        """
        self.driver.switch_to.window(window_name)

    def tag_name(self, locator):
        """Get the element's tagName

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: tagName
        """
        return self.find_element(locator).tag_name

    @property
    def timeout(self):
        """Spydr webdriver timeout for implicitly_wait, page_load_timeout, and script_timeout

        Returns:
            [int]: Spydr webdriver timeout
        """
        return self.__timeout

    @timeout.setter
    def timeout(self, seconds):
        self.__timeout = seconds
        self.implicitly_wait = seconds
        self.page_load_timeout = seconds
        self.script_timeout = seconds

    @staticmethod
    def timestamp(prefix='', suffix=''):
        """Get current local timestamp with optional prefix and/or suffix.

        Keyword Arguments:
            prefix (str, optional): Prefix for timestamp. Defaults to ''.
            suffix (str, optional): Suffix for timestamp. Defaults to ''.

        Returns:
            str: Timestamp with optional prefix and suffix
        """
        timestamp = strftime(r'%Y%m%d%H%M%S', localtime())
        return f'{prefix}{timestamp}{suffix}'

    def text(self, locator):
        """The element's text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: The text of the element
        """
        return self.find_element(locator).text

    @property
    def title(self):
        """Get the title of the current page.

        Returns:
            str: Title of the current page
        """
        return self.driver.title

    def trigger(self, locator, event):
        """Trigger the given event on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            event (str): Event name
        """
        self.execute_script('''
            var element = arguments[0];
            var eventName = arguments[1];
            var event = new Event(eventName, {"bubbles": false, "cancelable": false});
            element.dispatchEvent(event);
        ''', self.find_element(locator), event)

    def wait_until(self, method, poll_frequency=0.5, ignored_exceptions=None):
        """Create a WebDriverWait instance and wait until the given method is evaluated to not False.

        Args:
            method (callable): Method to call

        Keyword Arguments:
            poll_frequency (float, optional): Sleep interval between method calls. Defaults to 0.5.
            ignored_exceptions (list[Exception], optional): Exception classes to ignore during calls. Defaults to None.

        Returns:
            Any applicable return from the method call
        """
        return self.wait(self.driver, self.timeout, poll_frequency, ignored_exceptions).until(method)

    def wait_until_alert_present(self):
        """Wait until alert is present.

        Returns:
            False/Alert: Return False if not present.  Return Alert if present.
        """
        return self.wait_until(lambda _: self.ec.alert_is_present)

    def wait_until_attribute_contains(self, locator, attribute, value):
        """Wait until the element's attribute contains the given value.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
            value (str): value to check

        Returns:
            bool: Whether value is found in the element's attribute
        """
        return self.wait_until(lambda _: value in self.find_element(locator).get_attribute(attribute))

    def wait_until_frame_available_and_switch(self, frame_locator):
        """Wait until the given frame is available and switch to it.

        Args:
            frame_locator (str/WebElement): The locator to identify the frame or WebElement
        """
        self.wait_until(lambda _: self._is_frame_switched(frame_locator))

    def wait_until_enabled(self, locator):
        """Wait until the element is enabled.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is enabled
        """
        return self.wait_until(lambda _: self.is_enabled(locator))

    def wait_until_not(self, method):
        """Create a WebDriverWait instance and wait until the given method is evaluated to False.

        Args:
            method (callable): Method to call

        Returns:
            Any applicable return from the method call
        """
        return self.wait(self.driver, self.timeout).until_not(method)

    def wait_until_not_visible(self, locator, seconds=2):
        """Wait until the element is not visible in the given seconds.

        Args:
            locator (str): The locator to identify the element

        Keyword Arguments:
            seconds (int, optional): Seconds to give up waiting. Defaults to 2.

        Returns:
            bool: Whether the element is not visible
        """
        self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda _: not self.find_element(locator))
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
            return True
        finally:
            self.implicitly_wait = self.timeout

    def wait_until_number_of_windows_to_be(self, number):
        """Wait until number of windows matches the given number.

        Args:
            number (int): Number of windows

        Returns:
            bool: Whether number of windows matching the given number
        """
        return self.wait_until(self.ec.number_of_windows_to_be(number))

    def wait_until_selected(self, locator):
        """Wait until the element is selected.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is selected
        """
        return self.wait_until(lambda _: self.is_selected(locator))

    def wait_until_selection_to_be(self, locator, is_selected):
        """Wait until the element's `selected` state to match the given state.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            is_selected (bool): Element's `selected` state

        Returns:
            bool: Whether the element's `selected` state matching the given state
        """
        return self.wait_until(lambda _: self.is_selected(locator) == is_selected)

    def wait_until_text_contains(self, locator, text):
        """Wait until the element's text contains the given text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to match

        Returns:
            bool: Whether the element's text containing the given text
        """
        return self.wait_until(lambda _: text in self.find_element(locator).text)

    def wait_until_text_excludes(self, locator, text):
        """Wait until the element's text to exclude the given text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to not match

        Returns:
            bool: Whether the element's text excluding the given text
        """
        return self.wait_until(lambda _: text not in self.find_element(locator).text)

    def wait_until_title_contains(self, title):
        """Wait until the title of the current page contains the given title.

        Args:
            title (str): Title to match

        Returns:
            bool: Whether the title containing the given title
        """
        return self.wait_until(self.ec.title_contains(title))

    def wait_until_url_contains(self, url):
        """Wait until the URL of the current window contains the given URL.

        Args:
            url (str): URL to match

        Returns:
            bool: Whether the URL containing the given URL
        """
        return self.wait_until(self.ec.url_contains(url))

    def wait_until_visible(self, locator):
        """Wait until the element is visible.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is visible
        """
        return self.wait_until(lambda _: self.is_displayed(locator))

    @property
    def window_handle(self):
        """Return the handle of the current window.

        Returns:
            str: The current window handle
        """
        return self.driver.current_window_handle

    @property
    def window_handles(self):
        """Return the handles of all windows within the current session.

        Returns:
            list[str]: List of all window handles
        """
        return self.driver.window_handles

    def zoom(self, scale):
        """Set the zoom factor of a document defined by the viewport.

        Args:
            scale (float/str): Zoom factor: 0.8, 1.5, or '150%'
        """
        self.execute_script('document.body.style.zoom = arguments[0];', scale)

    def _abs_filename(self, filename, suffix='.png', root=None):
        if not filename.lower().endswith(suffix):
            filename += suffix

        abspath = os.path.abspath(
            os.path.join(root or self.screen_root, self._slugify(filename)))
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

    def _is_element_clicked(self, locator):
        try:
            element = self.find_element(locator)
            if not element.is_displayed() or not element.is_enabled():
                return False
            element.click()
            return True
        except (NoSuchWindowException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
            return False

    def _is_frame_switched(self, locator):
        try:
            self.switch_to_frame(locator)
            return True
        except NoSuchFrameException:
            return False

    @staticmethod
    def _parse_locator(locator):
        how = what = None
        matched = re.search('^([A-Za-z_]+)=(.+)', locator)

        if matched is None:
            what = locator
            if locator.startswith(('.', '#', '[')):
                how = Spydr.hows['css']
            elif locator.startswith(('/', '(')):
                how = Spydr.hows['xpath']
        else:
            somehow, what = matched.group(1, 2)
            if somehow in Spydr.hows:
                how = Spydr.hows[somehow]

        if how is None:
            raise InvalidSelectorException(
                f'Failed to parse locator: {locator}')

        return how, what

    @staticmethod
    def _slugify(s):
        s = str(s).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.]', '', s)


#
# --- WebElement Method Override ---
#
# Override WebElement.find_element and WebElement.find_elements to make sure
# Spydr locator formats (Spydr._parse_locator) are accepted by WebElement as well.
#
def _new_web_element_find_element(self, locator):
    how, what = Spydr._parse_locator(locator)
    return self._execute(Command.FIND_CHILD_ELEMENT, {"using": how, "value": what})['value']


def _new_web_element_find_elements(self, locator):
    how, what = Spydr._parse_locator(locator)
    return self._execute(Command.FIND_CHILD_ELEMENTS,  {"using": how, "value": what})['value']


WebElement.find_element = _new_web_element_find_element
WebElement.find_elements = _new_web_element_find_elements
