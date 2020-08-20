import base64
import inspect
import json
import logging
import os
import random
import re
import string
import urllib.parse
import zipfile

from datetime import date, timedelta
from functools import wraps
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from time import strftime, localtime
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import IEDriverManager, EdgeChromiumDriverManager

from .utils import INI, HOWS, Utils, YML


# Spydrify WebElement
class _WebElementSpydrify:
    def __call__(self, fn):
        @wraps(fn)
        def wrapper(spydr_or_element_self, *args, **kwargs):
            element_or_elements = fn(spydr_or_element_self, *args, **kwargs)
            element_or_elements = self._spydrify(spydr_or_element_self, element_or_elements)
            return element_or_elements
        return wrapper

    @classmethod
    def _spydrify(cls, spydr_or_element_self, element_or_elements):
        if isinstance(element_or_elements, WebElement):
            element_or_elements = SpydrElement(spydr_or_element_self, element_or_elements)
        elif isinstance(element_or_elements, (list, tuple)):
            for index, element in enumerate(element_or_elements):
                element_or_elements[index] = cls._spydrify(spydr_or_element_self, element)
        return element_or_elements


class Spydr:
    """Spydr WebDriver

    Keyword Arguments:
        auth_username (str): Username for HTTP Basic/Digest Auth. Defaults to None.
        auth_password (str): Password for HTTP Basic/Digest Auth. Defaults to None.
        browser (str): Browser to drive. Defaults to 'chrome'.
            Supported browsers: 'chrome', 'edge', 'firefox', 'ie', 'safari'.
        headless (bool): Headless mode. Defaults to False.
        ini (str/INI): INI File. Defaults to None.
        locale (str): Browser locale. Defaults to 'en'.
        log_indent (int): Indentation for logging messages. Defaults to 2.
        log_level (str): Logging level: 'INFO' or 'DEBUG'. Defaults to None.
            When set to 'INFO', `info()` messages will be shown.
            When set to 'DEBUG', `debug()`, `info()` and called methods will be shown.
        screen_root (str): The directory of saved screenshots. Defaults to './screens'.
        timeout (int): Timeout for implicitly_wait, page_load_timeout, and script_timeout. Defaults to 30.
        window_size (str): The size of the window when headless. Defaults to '1280,720'.
        yml (str/bytes/os.PathLike/YML): YAML File. Defaults to None.

    Raises:
        InvalidSelectorException: Raise an error when locator is invalid
        NoSuchElementException: Raise an error when no element is found
        WebDriverException: Raise an error when Spydr encounters an error

    Returns:
        Spydr: An instance of Spydr Webdriver
    """

    keys = Keys
    """selenium.webdriver.common.keys.Keys: Pre-defined keys codes"""

    wait = WebDriverWait
    """selenium.webdriver.support.ui.WebDriverWait: WebDriverWait"""

    def __init__(self,
                 auth_username=None,
                 auth_password=None,
                 browser='chrome',
                 headless=False,
                 ini=None,
                 locale='en',
                 log_indent=2,
                 log_level=None,
                 screen_root='./screens',
                 timeout=30,
                 window_size='1280,720',
                 yml=None):
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.browser = browser.lower()
        self.headless = headless
        self.ini = ini
        self.log_indent = log_indent if isinstance(log_indent, int) else 2
        self.log_level = logging.getLevelName(log_level) if log_level in ['DEBUG', 'INFO'] else 50
        self.screen_root = screen_root
        self.window_size = window_size
        self.yml = yml
        self.locale = self._format_locale(locale)
        self.driver = self._get_webdriver()
        self.logger = self._get_logger()
        self.timeout = timeout

    def abspath(self, filename, suffix=None, root=os.getcwd(), mkdir=True):
        """abspath(filename, suffix='.png', root=os.getcwd(), mkdir=True)
        Resolve file to absolute path and create all directories if missing.

        Args:
            filename (str): File name

        Keyword Arguments:
            suffix (str): File suffix. Defaults to None.
            root (str): Root directory. Defaults to `os.getcwd()`.
            mkdir (bool): Create directores in the path. Defaults to True.

        Returns:
            str: Absolute path of the file
        """
        return Utils.to_abspath(filename, suffix=suffix, root=root, mkdir=mkdir)

    def actions(self):
        """Initialize an ActionChains.

        Returns:
            ActionChains: An instance of ActionChains
        """
        return ActionChains(self.driver)

    def add_class(self, locator, class_name):
        """Add the given CSS class to the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name
        """
        self.find_element(locator).add_class(class_name)

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
            alert (Alert): Alert instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.accept()
        else:
            self.switch_to_alert().accept()

    def alert_dismiss(self, alert=None):
        """Dismiss the alert available.

        Keyword Arguments:
            alert (Alert): Alert instance. Defaults to None.
        """
        if isinstance(alert, Alert):
            alert.dismiss()
        else:
            self.switch_to_alert().dismiss()

    def alert_sendkeys(self, keys_to_send, alert=None, accept=True):
        """Send keys to the alert available and accept it.

        Args:
            keys_to_send (str): Text to send

        Keyword Arguments:
            alert (Alert): Alert instance. Defaults to None.
            accept (bool): Whether to accept the alert after sending keys.
        """
        alert = alert if isinstance(alert, Alert) else self.switch_to_alert()

        alert.send_keys(keys_to_send)

        if accept:
            alert.accept()

    def alert_text(self, alert=None, dismiss=True):
        """Get the text of the alert available and dismiss it.

        Keyword Arguments:
            alert (Alert): Alert Instance. Defaults to None.
            dismiss (bool): Whether to dismiss the alert.
        """
        alert = alert if isinstance(alert, Alert) else self.switch_to_alert()
        text = alert.text

        if dismiss:
            alert.dismiss()

        return text

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
        self.find_element(locator).blur()

    def css_property(self, locator, name):
        """The value of CSS property.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            name (str): CSS property name

        Returns:
            str: CSS property value
        """
        return self.find_element(locator).css_property(name)

    def checkbox_to_be(self, locator, is_checked, method='click'):
        """Set the checkbox, identified by the locator, to the given state (is_checked).

        Args:
            locator (str/WebElement): The locator to identify the checkbox or WebElement
            is_checked (bool): whether the checkbox is to be checked

        Keyword Arguments:
            method (str): Methods to toggle checkbox: `click`, `space`. 
                Use `space` when the element can not be clicked. Defaults to 'click'.

        Raises:
            InvalidSelectorException: Raise an error when the element is not a checkbox
            WebDriverException: Raise an error when unknown method is specified
        """
        element = self.find_element(locator)

        if element.tag_name != 'input' and element.get_attribute('type') != 'checkbox':
            raise InvalidSelectorException(
                f'Element is not a checkbox: {locator}')

        if element.is_selected() != is_checked and element.is_enabled():
            if method == 'click':
                self.js_click(element)
            elif method == 'space':
                element.send_keys(self.keys.SPACE)
            else:
                raise WebDriverException(f'Unknown method: {method}')

    def checkboxes_to_be(self, locator, is_checked, method='click', only_on_values=None):
        """Set all checkboxes, identified by the locator, to the given state (is_checked).

        Args:
            locator (str): The locator to identify all the checkboxes
            is_checked (bool): whether the checkboxes are to be checked

        Keyword Arguments:
            method (str): Methods to toggle checkbox: `click`, `space`. 
                Use `space` when the element can not be clicked. Defaults to 'click'.
            only_on_values (list/tuple): When given, only checkboxes with values in the list are set to `is_checked`
                while others are set to `not is_checked`. Defaults to None.
        """
        elements = self.find_elements(locator)

        for element in elements:
            if isinstance(only_on_values, (list, tuple)) and element.value.strip() not in only_on_values:
                self.checkbox_to_be(element, not is_checked, method=method)
            else:
                self.checkbox_to_be(element, is_checked, method=method)

    def children(self, locator):
        """Get the children elements of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            list[WebElement]: The children elements of the given element.
        """
        return self.find_element(locator).children

    def clear(self, locator):
        """Clear the text of a text input element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).clear()

    def clear_and_send_keys(self, locator, *keys, blur=False, wait_until_enabled=False):
        """Clear the element first and then send the given keys.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            *keys: Any combinations of strings

        Keyword Arguments:
            blur (bool): Lose focus after sending keys. Defaults to False.
            wait_until_enabled (bool): Whether to wait until the element `is_enabled()` before clearing and sending keys. Defaults to False.
        """
        self.find_element(locator).clear_and_send_keys(*keys, blur=blur, wait_until_enabled=wait_until_enabled)

    def click(self, locator, switch_to_new_target=False, scroll_into_view=False, behavior='auto'):
        """Click the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            switch_to_new_target (bool): Whether to switch to a newly-opened window after clicking. Defautls to False.
            scroll_into_view (bool): Whether to scroll the element into view before clicking. Defaults to False.
            behavior (str): Defines the transition animation for `scroll_into_view`.
                One of `auto` or `smooth`. Defaults to 'auto'.

        Returns:
            tuple, optional: If `switch_to_new_target`, it returns a tuple of (window_handle_before_clicking, window_handle_after_clicking)
        """
        if switch_to_new_target:
            window_handle_before_clicking = self.window_handle
            num_of_windows = len(self.window_handles)

        self.wait_until(lambda _: self._is_clicked(locator, scroll_into_view=scroll_into_view, behavior=behavior))

        if switch_to_new_target:
            self.wait_until_number_of_windows_to_be(num_of_windows + 1)
            window_handle_after_clicking = self.window_handles[-1]
            self.switch_to_window(window_handle_after_clicking)
            return (window_handle_before_clicking, window_handle_after_clicking)

    def click_with_offset(self, locator, x_offset=1, y_offset=1):
        """Click the element from x and y offsets.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            x_offset (int): X offset from the left of the element. Defaults to 1.
            y_offset (int): Y offset from the top of the element. Defaults to 1.
        """
        element = self.find_element(locator)
        self.wait_until_enabled(element)
        self.actions().move_to_element_with_offset(
            element, x_offset, y_offset).click().perform()

    def close(self):
        """Close the window."""
        self.driver.close()

    def close_all_others(self):
        """Close all other windows."""
        windows = self.window_handles

        if len(windows) > 1:
            current_window = self.window_handle

            for window in windows:
                if window == current_window:
                    continue
                self.switch_to_window(window)
                self.close()

            self.switch_to_window(current_window)

    def ctrl_click(self, locator):
        """Ctrl-click the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        element = self.find_element(locator)
        control = self.keys.CONTROL

        self.actions().key_down(control).click(element).key_up(control).perform()

    @property
    def current_url(self):
        """Get the URL of the current page.

        Returns:
            str: URL of the page
        """
        return self.driver.current_url

    def date_from_delta(self, days, format=r'%m/%d/%Y'):
        """Get the date by the given delta from today.

        Args:
            days (int): Delta days from today

        Keyword Arguments:
            format (str): Date format. Defaults to '%m/%d/%Y'.

        Returns:
            str: Delta date from today

        Examples:
            | date_today() # 2020/12/10
            | date_from_delta(1) # 2020/12/11
            | date_from_delta(-1) # 2020/12/09
        """
        delta = date.today() + timedelta(days=days)
        return delta.strftime(format)

    def date_today(self, format=r'%m/%d/%Y'):
        """Get Today's date.

        Keyword Arguments:
            format (str): Date format. Defaults to '%m/%d/%Y'.

        Returns:
            str: Today's date in the given format
        """
        return date.today().strftime(format)

    def debug(self, message):
        """Log **DEBUG** messages.

        Args:
            message (str): **DEBUG** message
        """
        self.logger.debug(message)

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

    @property
    def driver(self):
        """Instance of Selenium WebDriver.

        Returns:
            WebDriver: Instance of Selenium WebDriver
        """
        return self.__driver

    @driver.setter
    def driver(self, driver_):
        self.__driver = driver_

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

    @_WebElementSpydrify()
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

        if how == HOWS['css']:
            matched = re.search(r'(.*):eq\((\d+)\)', what)
            if matched:
                new_what, nth = matched.group(1, 2)
                try:
                    element = self.find_elements(f'css={new_what}')[int(nth)]
                except IndexError:
                    raise NoSuchElementException(f'{locator} does not have {nth} element')

        if not element:
            element = self.wait_until(lambda _: self.is_located(locator))

            if not isinstance(element, WebElement):
                raise NoSuchElementException(f'Cannot locate element in the given time using: {locator}')

        return element

    @_WebElementSpydrify()
    def find_elements(self, locator):
        """Find all elements by the given locator.

        Args:
            locator (str): The locator to identify the elements or list[WebElement]

        Returns:
            list[WebElement]: All elements found
        """
        if isinstance(locator, (list, tuple)) and all(isinstance(el, WebElement) for el in locator):
            return locator

        how, what = self._parse_locator(locator)
        elements = self.driver.find_elements(how, what)

        return elements

    def first_child(self, locator):
        """Get the first child element of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: The first child element of the given element.
        """
        return self.find_element(locator).first_child

    def focus(self, locator):
        """Trigger focus event on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).focus()

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

    def get_ini_key(self, key, section=None):
        """Get value of the given key from INI.

        Args:
            key (str): Key name
            section: INI section. Defaults to the default section.

        Returns:
            Value (any data type JSON supports)
        """
        if self.ini:
            return self.ini.get_key(key, section)

    def get_property(self, locator, name):
        """Get the given property of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            name (str): Property name

        Returns:
            bool/dict/int/list/str/None: The property value
        """
        return self.find_element(locator).get_property(name)

    def get_screenshot_as_base64(self):
        """Get a screenshot of the current window as a base64 encoded string.

        Returns:
            str: Base64 encoded string of the screenshot
        """
        self.wait_until_page_loaded()
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_as_file(self, filename):
        """Save a screenshot of the current window to filename (PNG).

        Default directory for saved screenshots is defined in: screen_root.

        Args:
            filename (str): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        self.wait_until_page_loaded()
        return self.driver.get_screenshot_as_file(self.abspath(filename, suffix='.png', root=self.screen_root))

    def get_screenshot_as_png(self):
        """Get a screenshot of the current window as a binary data.

        Returns:
            bytes: Binary data of the screenshot
        """
        self.wait_until_page_loaded()
        return self.driver.get_screenshot_as_png()

    def get_window_position(self, window_handle='current'):
        """Get the x and y position of the given window.

        Keyword Arguments:
            window_handle (str): The handle of the window. Defaults to 'current'.

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
            window_handle (str): The handle of the window. Defaults to 'current'.

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
        return self.find_element(locator).has_attribute(attribute)

    def has_class(self, locator, class_name):
        """Check if the element has the given CSS class.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name

        Returns:
            bool: Whether the CSS class exists
        """
        return self.find_element(locator).has_class(class_name)

    def hide(self, locator):
        """Hide the element."""
        self.find_element(locator).hide()

    def highlight(self, locator, hex_color='#ff3'):
        """Highlight the element with the given color.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            hex_color (str, optional): Hex color. Defaults to '#ff3'.
        """
        self.find_element(locator).highlight(hex_color)

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

    def info(self, message):
        """Log **INFO** messages.

        Args:
            message (str): **INFO** Message
        """
        self.logger.info(message)

    @property
    def ini(self):
        """INI file as an INI instance.

        Returns:
            INI: INI instance
        """
        return self.__ini

    @ini.setter
    def ini(self, file):
        if isinstance(file, INI):
            self.__ini = file
        else:
            self.__ini = INI(file) if file else None

    def is_displayed(self, locator):
        """Check if the element is displayed.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is displayed
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

    def is_located(self, locator, seconds=None):
        """Check if the element is located in the given seconds.

        Args:
            locator (str): The locator to identify the element

        Keyword Arguments:
            seconds (int): Seconds to wait until giving up. Defaults to `self.implicitly_wait`.

        Returns:
            False/WebElement: Return False if not located. Return WebElement if located.
        """
        how, what = self._parse_locator(locator)

        orig_implicitly_wait = self.implicitly_wait
        seconds = seconds if seconds else orig_implicitly_wait

        if seconds != orig_implicitly_wait:
            self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda wd: wd.find_element(how, what))
        except (NoSuchElementException, NoSuchWindowException, StaleElementReferenceException, TimeoutException):
            return False
        finally:
            if seconds != orig_implicitly_wait:
                self.implicitly_wait = orig_implicitly_wait

    def is_page_loaded(self):
        """Check if `document.readyState` is `complete`.

        Returns:
            bool: Whether the page is loaded
        """
        return self.execute_script('return document.readyState == "complete";')

    def is_selected(self, locator):
        """Check if the element is selected.

        Can be used to check if a checkbox or radio button is selected.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is selected
        """
        return self.find_element(locator).is_selected()

    def is_text_in_element(self, locator, text):
        """Check if the element contains the given `text`.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to check

        Returns:
            bool: Whether the element has the given text
        """
        return text in self.find_element(locator).text

    def is_value_in_element_attribute(self, locator, attribute, value):
        """Check if the element's attribute contains the given `value`.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
            value (str): value to check

        Returns:
            bool: Whether value is found in the element's attribute
        """
        return value in self.find_element(locator).get_attribute(attribute)

    def js_click(self, locator):
        """Call `HTMLElement.click()` using JavaScript.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.execute_script('arguments[0].click();', self.find_element(locator))

    def last_child(self, locator):
        """Get the last child element of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: The last child element of the element element.
        """
        return self.find_element(locator).last_child

    def load_cookies(self, filename):
        """Load Cookies from a JSON file.

        Args:
            filename (str): File name
        """
        file_ = self.abspath(filename, suffix='.json', mkdir=False)
        with open(file_, "r") as cookie_file:
            cookies = json.load(cookie_file)
            for cookie in cookies:
                self.add_cookie(cookie)

    def location(self, locator):
        """The location of the element in the renderable canvas.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The location of the element as dict: {'x': 0, 'y': 0}
        """
        return self.find_element(locator).location

    def maximize_window(self):
        """Maximize the current window."""
        if not self.headless:
            self.driver.maximize_window()

    def maximize_to_screen(self):
        """Maximize the current window to match the screen size."""
        size = self.execute_script('return { width: window.screen.width, height: window.screen.height };')
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
            x_offset (int): X offset. Defaults to 1.
            y_offset (int): Y offset. Defaults to 1.
        """
        element = self.find_element(locator)
        self.actions().move_to_element_with_offset(element, x_offset, y_offset).perform()

    def next_element(self, locator):
        """Get the next element of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: The next element of the given element.
        """
        return self.find_element(locator).next_element

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

    def open(self, url, new_tab=False):
        """Load the web page by its given URL.

        Args:
            url (str): URL of the web page

        Keyword Arguments:
            new_tab (bool): Whether to open in a new tab. Defaults to False.

        Returns:
            list[str]: List of [current_window_handle, new_tab_window_handle]
        """
        current_handle = self.window_handle

        if new_tab:
            new_handle = self.new_tab()
            self.switch_to_window(new_handle)

        self.driver.get(url)

        return [current_handle, new_handle] if new_tab else [current_handle, None]

    def open_data_as_url(self, data, mediatype='text/html', encoding='utf-8'):
        """Use Data URL to open `data` as inline document.

        Args:
            data (str): Data to be open as inline document

        Keyword Arguments:
            mediatype (str): MIME type. Defaults to 'text/html'.
            encoding (str): Data encoding. Defaults to 'utf-8'.
        """
        base64_encoded = base64.b64encode(bytes(data, encoding))
        base64_data = str(base64_encoded, encoding)
        self.open(f'data:{mediatype};base64,{base64_data}')

    def open_file(self, filename):
        """Open file with the browser.

        Args:
            filename (str): File name

        Raises:
            WebDriverException: Raise an error when filename is not found
        """
        file_ = self.abspath(filename, mkdir=False)

        if os.path.isfile(file_):
            html_path = file_.replace('\\', '/')
            self.open(f'file:///{html_path}')
        else:
            raise WebDriverException(f'Cannot find file: ${file_}')

    def open_file_as_url(self, filename, mediatype='text/html', encoding='utf-8'):
        """Use Data URL to open file content as inline document.

        Args:
            filename (str): File name

        Keyword Arguments:
            mediatype (str): MIME type. Defaults to 'text/html'.
            encoding (str): File encoding. Defaults to 'utf-8'.

        Raises:
            WebDriverException: Raise an error when filename is not found
        """
        file_ = self.abspath(filename, mkdir=False)

        if os.path.isfile(file_):
            data = open(file_, 'r', encoding=encoding).read()
            self.open_data_as_url(data, mediatype=mediatype, encoding=encoding)
        else:
            raise WebDriverException(f'Cannot find file: ${file_}')

    def open_with_auth(self, url, username=None, password=None):
        """Load the web page by adding username and password to the URL

        Args:
            url (str): URL of the web page

        Keyword Arguments:
            username (str): Username. Defaults to auth_username or None.
            password (str): Password. Defaults to auth_password or None.
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

    def parent_element(self, locator):
        """Get the parent element of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: The parent element of the given element.
        """
        return self.find_element(locator).parent_element

    def previous_element(self, locator):
        """Get the previous element of the given element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: The previous element of the given element.
        """
        return self.find_element(locator).previous_element

    def quit(self):
        """Quit the Spydr webdriver."""
        self.driver.quit()

    def radio_to_be(self, locator, is_checked, method='click'):
        """Set the radio button, identified by the locator, to the given state (is_checked).

        Args:
            locator (str/WebElement): The locator to identify the radio button or WebElement
            is_checked (bool): whether the radio button is to be checked

        Keyword Arguments:
            method (str): Methods to toggle checkbox: `click`, `space`. 
                Use `space` when the element can not be clicked. Defaults to 'click'.

        Raises:
            WebDriverException: Raise an error when unknown method is specified
        """
        radio = self.find_element(locator)

        if is_checked:
            if not radio.is_selected() and radio.is_enabled():
                if method == 'click':
                    self.click(radio)
                elif method == 'space':
                    radio.send_keys(self.keys.SPACE)
                else:
                    raise WebDriverException(f'Unknown method: {method}')
        else:
            if radio.is_selected() and radio.is_enabled():
                self.execute_script('arguments[0].checked = false;', radio)

    def randomized_string(self, size=10, sequence=string.ascii_letters + string.digits, is_upper=False):
        """Generate a randomized string in the given size using the given characters.

        Args:
            size (int, optional): Size of the string. Defaults to 10.

        Keyword Arguments:    
            sequence (str): Sequence. Defaults to string.ascii_letters+string.digits.
            is_upper (bool): Uppercase the randomized string. Defaults to False.

        Returns:
            [type]: [description]
        """
        string_ = ''.join(random.choice(sequence) for _ in range(size))

        return string_.upper() if is_upper else string_

    def rect(self, locator):
        """Get the size and location of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The size and location of the element as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.find_element(locator).rect

    def refresh(self):
        """Refresh the current page."""
        self.driver.refresh()

    def refresh_until_page_changed(self, frequency=2, timeout=10, body_text_diff=True):
        """Refresh the page (every `frequency`) until the page changes or until `timeout`.

        Keyword Arguments:
            frequency (int): Refresh frequency
            timeout (int): Time allowed to refresh. Defaults to 10.
            body_text_diff (bool): Compare `body` text when True.  Compare `page_source` when False.

        Returns:
            bool: Whether the page is changed
        """
        return self.wait(self.driver, timeout, poll_frequency=frequency).until(lambda _: self._is_page_changed_after_refresh(body_text_diff))

    def remove_attribute(self, locator, attribute):
        """Remove the given attribute from the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
        """
        self.find_element(locator).remove_attribute(attribute)

    def remove_class(self, locator, class_name):
        """Remove the given CSS class to the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name
        """
        self.find_element(locator).remove_class(class_name)

    def remove_file(self, file):
        """Remove the file.

        Args:
            file (str): File path
        """
        file = self.abspath(file, mkdir=False)

        if os.path.exists(file):
            os.remove(file)

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
            x_offset (int): X offset from the left of the element. Defaults to 1.
            y_offset (int): Y offset from the top of the element. Defaults to 1.
        """
        element = self.find_element(locator)

        self.actions().move_to_element_with_offset(element, x_offset, y_offset).context_click().perform()

    def save_cookies(self, filename):
        """Save cookies as a JSON file.

        Args:
            filename (str): File name
        """
        file_ = self.abspath(filename, suffix='.json')
        with open(file_, "w") as cookie_file:
            json.dump(self.get_cookies(), cookie_file, indent=2)

    def save_ini(self):
        """Save INI file."""
        if self.ini:
            self.ini.save()

    def save_screenshot(self, filename):
        """Save a screenshot of the current window to filename (PNG).

        Default directory for saved screenshots is defined in: screen_root.

        Args:
            filename (str): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        self.wait_until_page_loaded()
        return self.driver.save_screenshot(self.abspath(filename, suffix='.png', root=self.screen_root))

    def screenshot(self, locator, filename):
        """Save a screenshot of the element to the filename (PNG).

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            filename ([type]): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        return self.find_element(locator).save_screenshot(filename)

    def screenshot_as_base64(self, locator):
        """Get the screenshot of the element as a Base64 encoded string

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: Base64 encoded string of the screenshot
        """
        return self.find_element(locator).screenshot_as_base64

    def screenshot_as_png(self, locator):
        """Get the screenshot of the element as a binary data.

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

    def scroll_into_view(self, locator, behavior="auto", block="start", inline="nearest"):
        """Scroll the element's parent to be displayed.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            behavior (str): Defines the transition animation. One of `auto` or `smooth`. Defaults to 'auto'.
            block (str): Defines vertical alignment. One of `start`, `center`, `end`, or `nearest`. Defaults to 'start'.
            inline (str): Defines horizontal alignment. One of `start`, `center`, `end`, or `nearest`. Defaults to 'nearest'.
        """
        self.find_element(locator).scroll_into_view(behavior=behavior, block=block, inline=inline)

    def scroll_to(self, locator, x, y):
        """Scroll the elment to the given x- and y-coordinates. (IE not supported)

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            x (int): x-coordinate
            y (int): y-coordinate
        """
        self.find_element(locator).scroll_to(x, y)

    def select_to_be(self, select_locator, option_value, selected=True, option_by='value'):
        """Set `selected` state of the given `option` in the `select` drop-down menu.

        Args:
            select_locator (str/WebElement): The locator to identify the element or WebElement
            option_value (int/str): The value to identify the option by using `option_by` method.

        Keyword Arguments:
            selected (bool): Option `selected` state to be
            option_by (str): The method to identify the option. One of `value`, `text`, or `index`. Defaults to 'value'.

        Raises:
            InvalidSelectorException: Raise an error when the element is not a select

        Examples:
            | # Deselect option: <option value="3">Three</option>
            | select_to_be('#group', 3, selected=False)
            | # Select option: <option value="5">Volvo</option>
            | select_to_be('#car', 'Volvo', option_by='text')
        """
        select = self.wait_until(lambda _: self._is_selectable(select_locator))
        option = None

        if not select:
            raise WebDriverException(f'Select has no option: {select_locator}')

        if option_by == 'value':
            option = select.find_element(f'[value="{option_value}"]')
        elif option_by == 'text':
            option = select.find_element(f'//*[text()="{option_value}"]')
        elif option_by == 'index':
            options = select.find_elements('tag_name=option')
            index = int(option_value)
            option = options[index] if index < len(options) else None

        if not option:
            raise WebDriverException(f'Cannot using "{option_by}" to identify the option: {option_value}')

        if option.is_selected() != selected:
            self.click(option)

    def select_to_be_random(self, select_locator, ignored_options=[None, "", "0"]):
        """Randomly select an `option` in the `select` menu

        Args:
            select_locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            ignored_options (list): Options to exlcude from selection. Defaults to [None, "", "0"].

        Raises:
            WebDriverException: Raise an error if failing to randomly select an option
        """
        select = self.wait_until(lambda _: self._is_selectable(select_locator))

        if not select:
            raise WebDriverException(f'Select has no option: {select_locator}')

        options = select.find_elements('css=option')

        random_option = self._random_option(options, ignored_options=ignored_options)

        if random_option:
            random_option.click()
        else:
            raise WebDriverException(f'Cannot randomly select an option in: {select_locator}')

    def select_to_be_all(self, select_locator):
        """Select all `option` in a **multiple** `select` drop-down menu.

        Args:
            select_locator (str/WebElement): The locator to identify the element or WebElement
        """
        select = self.find_element(select_locator)
        self._multiple_select_to_be(select, True)

    def select_to_be_none(self, select_locator):
        """De-select all `option` in a **multiple** `select` drop-down menu.

        Args:
            select_locator (str/WebElement): The locator to identify the element or WebElement
        """
        select = self.find_element(select_locator)
        self._multiple_select_to_be(select, False)

    def selected_options(self, select_locator, by='value'):
        """Get values of **selected** `option` in a `select` drop-down menu.

        Args:
            select_locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            by (str): Get selected options by `value`, `text`, or `index`. Defaults to 'value'.

        Raises:
            InvalidSelectorException: Raise an error when element is not a select element
            WebDriverException: Raise an error when the given `by` is unsupported

        Returns:
            list[int/str]: list of values of all selected options
        """
        select = self.find_element(select_locator)
        options = []

        if select.tag_name != 'select':
            raise InvalidSelectorException(f'Element is not a select: {select_locator}')

        if self.browser == 'ie':
            multiple = select.get_attribute('multiple')

            for option in select.find_elements('tag_name=option'):
                if option.is_selected():
                    options.append(option)
                    if not multiple:
                        break
        else:
            options.extend(select.selectedOptions())

        if by == 'value':
            return [opt.value for opt in options]
        elif by == 'text':
            return [opt.text for opt in options]
        elif by == 'index':
            return [opt.get_property('index') for opt in options]
        else:
            raise WebDriverException(f'Unsupported selected options by: {by}')

    def send_keys(self, locator, *keys, blur=False, wait_until_enabled=False):
        """Simulate typing into the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            *keys: Any combinations of strings

        Keyword Arguments:
            blur (bool): Lose focus after sending keys. Defaults to False.
            wait_until_enabled (bool): Whether to wait until the element `is_enabled()` before sending keys. Defaults to False.
        """
        self.find_element(locator).send_keys(*keys, blur=blur, wait_until_enabled=wait_until_enabled)

    def set_attribute(self, locator, attribute, value):
        """Set the given value to the attribute of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
            value (str): Attribute name
        """
        self.find_element(locator).set_attribute(attribute, value)

    def set_ini_key(self, key, value, section=None):
        """Set the value of the given key in INI.

        Args:
            key (str): Key name
            value: Value (any data type JSON supports)
            section: INI section. Defaults to the default section.
        """
        if self.ini:
            self.ini.set_key(key, value, section)

    def set_window_position(self, x, y, window_handle='current'):
        """Set the x and y position of the current window

        Args:
            x (int): x-coordinate in pixels
            y (int): y-coordinate in pixels

        Keyword Arguments:
            window_handle (str): Window handle. Defaults to 'current'.

        Returns:
            dict: Window rect as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.set_window_position(x, y, window_handle)

    def set_window_rect(self, x=None, y=None, width=None, height=None):
        """Set the x, y, width, and height of the current window.

        Keyword Arguments:
            x (int): x-coordinate in pixels. Defaults to None.
            y (int): y-coordinate in pixels. Defaults to None.
            width (int): Window width in pixels. Defaults to None.
            height (int): Window height in pixels. Defaults to None.

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
            window_handle (str): Window handle. Defaults to 'current'.

        Returns:
            dict: Window rect as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return self.driver.set_window_size(width, height, window_handle)

    def shift_click_from_and_to(self, from_locator, to_locator):
        """Shift click from `from_locator` to `to_locator`.

        Args:
            from_locator (str/WebElement): The locator to identify the element or WebElement
            to_locator (str/WebElement): The locator to identify the element or WebElement
        """
        from_element = self.find_element(from_locator)
        to_element = self.find_element(to_locator)
        shift = self.keys.SHIFT

        self.actions().key_down(shift).click(from_element).click(to_element).key_up(shift).perform()

    def show(self, locator):
        """Show the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).show()

    def size(self, locator):
        """The size of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            dict: The size of the element as dict: {'width': 100, 'height': 100}
        """
        return self.find_element(locator).size

    def sleep(self, seconds):
        """Sleep the given seconds.

        Args:
            seconds (int): Seconds to sleep
        """
        try:
            self.wait(self.driver, seconds).until(lambda _: False)
        except:
            pass

    def submit(self, locator):
        """Submit a form.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
        """
        self.find_element(locator).submit()

    def switch_to_active_element(self):
        """Switch to active element.

        Returns:
            WebElement: Active Element
        """
        return self.driver.switch_to.active_element

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
            False/WebElement: Return False if not located. Return WebElement if located.
        """
        self.wait_until_frame_available_and_switch(frame_locator)
        return self.wait_until(lambda _: self.is_located(element_locator))

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

    def t(self, key, **kwargs):
        """Get value from YML instance by using "dot notation" key.

        Args:
            key (str): Dot notation key

        Keyword Arguments:
            **kwargs: Format key value (str) with `str.format(**kwargs)`.

        Returns:
            value of dot notation key

        Examples:
            | # YAML
            | today:
            |   dashboard:
            |     search: '#search'
            |     name: 'Name is {name}'
            |
            | t('today.dashboard.search') # '#search'
            | t('today.dashboard.name', name='Spydr') # 'Name is Spydr'
        """
        return self.yml.t(key, **kwargs)

    def tag_name(self, locator):
        """Get the element's tagName.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: tagName
        """
        return self.find_element(locator).tag_name

    def text(self, locator, typecast=str):
        """The the element's text. (Only works when the element is in the viewport)

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            typecast: Typecast the text. Defaults to `str`.

        Returns:
            The text, by `typecast`, of the element
        """
        return typecast(self.find_element(locator).text)

    def text_content(self, locator):
        """Get the element's text. (Works whether the element is in the viewport or not)

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            str: The text of the element
        """
        return self.find_element(locator).text_content

    def texts(self, locator, typecast=str):
        """All Elements' text.

        Args:
            locator (str): The locator to identify the elements or list[WebElement]

        Keyword Arguments:
            typecast: Typecast the texts. Defaults to `str`.

        Returns:
            list: list of texts, by `typecast`, of the given elements
        """
        return [typecast(element.text) for element in self.find_elements(locator)]

    def text_to_file(self, text, filename, suffix):
        """Write text to the given filename

        Args:
            text (str): Text to write
            filename (str): filename of the text file
            suffix (str): suffix of the text file

        Returns:
            str: Absolute path of the file
        """
        file_ = self.abspath(filename, suffix=suffix)

        with open(file_, 'w') as text_file:
            text_file.write(text)

        return file_

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
            prefix (str): Prefix for timestamp. Defaults to ''.
            suffix (str): Suffix for timestamp. Defaults to ''.

        Returns:
            str: Timestamp with optional prefix and suffix
        """
        timestamp = strftime(r'%Y%m%d%H%M%S', localtime())
        return f'{prefix}{timestamp}{suffix}'

    @property
    def title(self):
        """Get the title of the current page.

        Returns:
            str: Title of the current page
        """
        return self.driver.title

    def toggle_attribute(self, locator, name):
        """Toggle a Boolean attribute of the given element. (IE not supported)

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            name ([type]): Attribute name
        """
        self.find_element(locator).toggle_attribute(name)

    def toggle_class(self, locator, class_name):
        """Toggole the given CSS class of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name
        """
        self.find_element(locator).toggle_class(class_name)

    def trigger(self, locator, event):
        """Trigger the given event on the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            event (str): Event name
        """
        self.find_element(locator).trigger(event)

    def value(self, locator, typecast=str):
        """Get the value of the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Keyword Arguments:
            typecast: Typecast the value. Defaults to `str`.

        Returns:
            The value, by `typecast`, of the element
        """
        return typecast(self.find_element(locator).value)

    def values(self, locator, typecast=str):
        """Get the values of the elements.

        Args:
            locator (str): The locator to identify the elements or list[WebElement]

        Keyword Arguments:
            typecast: Typecast the values. Defaults to `str`.

        Returns:
            list: list of values, by `typecast`, of the given elements
        """
        return [typecast(element.value) for element in self.find_elements(locator)]

    def wait_until(self, method, timeout=None, poll_frequency=0.5, ignored_exceptions=[NoSuchElementException]):
        """Create a WebDriverWait instance and wait until the given method is evaluated to not False.

        Args:
            method (callable): Method to call

        Keyword Arguments:
            timeout (int): Timeout. Defaults to `self.timeout`.
            poll_frequency (float): Sleep interval between method calls. Defaults to 0.5.
            ignored_exceptions (list[Exception]): Exception classes to ignore during calls. Defaults to (NoSuchElementException).

        Returns:
            Any applicable return from the method call
        """
        timeout = int(timeout) if timeout is not None else self.timeout
        return self.wait(self.driver, timeout, poll_frequency, ignored_exceptions).until(method)

    def wait_until_alert_present(self):
        """Wait until alert is present.

        Returns:
            False/Alert: Return False if not present. Return Alert if present.
        """
        return self.wait_until(lambda _: expected_conditions.alert_is_present)

    def wait_until_attribute_contains(self, locator, attribute, value):
        """Wait until the element's attribute contains the given value.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            attribute (str): Attribute name
            value (str): value to check

        Returns:
            bool: Whether value is found in the element's attribute
        """
        return self.wait_until(lambda _: self.is_value_in_element_attribute(locator, attribute, value))

    def wait_until_class_contains(self, locator, class_name):
        """Wait until the element contains the given CSS class.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name

        Returns:
            bool: Whether the element contains the given CSS class
        """
        return self.wait_until(lambda _: self.has_class(locator, class_name))

    def wait_until_class_excludes(self, locator, class_name):
        """Wait until the element excludes the given CSS class.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            class_name (str): CSS class name

        Returns:
            bool: Whether the element excludes the given CSS class
        """
        return self.wait_until(lambda _: not self.has_class(locator, class_name))

    def wait_until_displayed(self, locator):
        """Wait until the element is displayed.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is displayed
        """
        return self.wait_until(lambda _: self.is_displayed(locator))

    def wait_until_displayed_and_get_elmement(self, locator):
        """Wait until the element is displayed and return the element.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            WebElement: WebElement
        """
        self.wait_until_displayed(locator)
        return self.find_element(locator)

    def wait_until_enabled(self, locator):
        """Wait until the element is enabled.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement

        Returns:
            bool: Whether the element is enabled
        """
        return self.wait_until(lambda _: self.is_enabled(locator))

    def wait_until_frame_available_and_switch(self, frame_locator):
        """Wait until the given frame is available and switch to it.

        Args:
            frame_locator (str/WebElement): The locator to identify the frame or WebElement
        """
        self.wait_until(lambda _: self._is_frame_switched(frame_locator))

    def wait_until_ignored_timeout(self, method, timeout=3):
        """Wait until the given method timed-out and ignore `TimeoutException`.

        Args:
            method ([type]): Method to call

        Keyword Arguments:
            timeout (int): [description]. Defaults to 3.

        Returns:
            Any applicable return from the method call
        """
        self.implicitly_wait = int(timeout)

        try:
            return self.wait_until(method, timeout=timeout)
        except TimeoutException:
            pass
        finally:
            self.implicitly_wait = self.timeout

    def wait_until_loading_finished(self, locator, seconds=2):
        """Wait until `loading` element shows up and then disappears.

        Args:
            locator (str/WebElement): The locator to identify the element

        Keyword Arguments:
            seconds (int): Seconds to give up waiting. Defaults to 2.

        Returns:
            bool: Whether the element is not displayed
        """
        how, what = self._parse_locator(locator)
        self.implicitly_wait = seconds

        try:
            self.wait(self.driver, seconds).until(lambda wd: wd.find_element(how, what))
            return self.wait(self.driver, seconds).until(lambda wd: not wd.find_element(how, what))
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
            return True
        finally:
            self.implicitly_wait = self.timeout

    def wait_until_not(self, method):
        """Create a WebDriverWait instance and wait until the given method is evaluated to False.

        Args:
            method (callable): Method to call

        Returns:
            Any applicable return from the method call
        """
        return self.wait(self.driver, self.timeout).until_not(method)

    def wait_until_not_displayed(self, locator, seconds=2):
        """Wait until the element is not displayed in the given seconds.

        Args:
            locator (str): The locator to identify the element

        Keyword Arguments:
            seconds (int): Seconds to give up waiting. Defaults to 2.

        Returns:
            bool: Whether the element is not displayed
        """
        how, what = self._parse_locator(locator)
        self.implicitly_wait = seconds

        try:
            return self.wait(self.driver, seconds).until(lambda wd: not wd.find_element(how, what))
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
        return self.wait_until(expected_conditions.number_of_windows_to_be(number))

    def wait_until_page_loaded(self):
        """Wait until `document.readyState` is `complete`."""
        self.wait_until(lambda _: self.is_page_loaded())

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
        return self.wait_until(lambda _: self.is_text_in_element(locator, text))

    def wait_until_text_equal_to(self, locator, text):
        """Wait until the element's text equal to the given text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to not match

        Returns:
            bool: Whether the element's text equal to the given text
        """
        return self.wait_until(lambda _: text == self.find_element(locator).text)

    def wait_until_text_excludes(self, locator, text):
        """Wait until the element's text to exclude the given text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to not match

        Returns:
            bool: Whether the element's text excluding the given text
        """
        return self.wait_until(lambda _: text not in self.find_element(locator).text)

    def wait_until_text_not_equal_to(self, locator, text):
        """Wait until the element's text not equal to the given text.

        Args:
            locator (str/WebElement): The locator to identify the element or WebElement
            text (str): Text to not match

        Returns:
            bool: Whether the element's text not equal to the given text
        """
        return self.wait_until(lambda _: text != self.find_element(locator).text)

    def wait_until_title_contains(self, title):
        """Wait until the title of the current page contains the given title.

        Args:
            title (str): Title to match

        Returns:
            bool: Whether the title containing the given title
        """
        return self.wait_until(expected_conditions.title_contains(title))

    def wait_until_url_contains(self, url, timeout=None):
        """Wait until the URL of the current window contains the given URL.

        Args:
            url (str): URL to match

        Keyword Arguments:
            timeout (int): Timeout. Defaults to `self.timeout`.

        Returns:
            bool: Whether the URL containing the given URL
        """
        timeout = int(timeout) if timeout is not None else self.timeout
        self.implicitly_wait = timeout

        try:
            return self.wait_until(expected_conditions.url_contains(url), timeout=timeout)
        except TimeoutException:
            return False
        finally:
            self.implicitly_wait = self.timeout

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

    @property
    def yml(self):
        """YAML file as YML instance.

        Returns:
            YML: YML instance
        """
        return self.__yml

    @yml.setter
    def yml(self, file):
        if isinstance(file, YML):
            self.__yml = file
        else:
            self.__yml = YML(file)

    def zoom(self, scale):
        """Set the zoom factor of a document defined by the viewport.

        Args:
            scale (float/str): Zoom factor: 0.8, 1.5, or '150%'
        """
        self.execute_script('document.body.style.zoom = arguments[0];', scale)

    def _auth_extension_as_base64(self, username, password):
        bytes_ = self._auth_extension_as_bytes(username, password)
        return base64.b64encode(bytes_).decode('ascii')

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
        filename = self.abspath('spydr_auth', suffix=suffix, root=self.extension_root)

        with open(filename, 'wb') as crx_file:
            crx_file.write(bytes_)

        return filename

    def _chrome_options(self):
        # https://chromium.googlesource.com/chromium/src/+/master/chrome/common/chrome_switches.cc
        # https://chromium.googlesource.com/chromium/src/+/master/chrome/common/pref_names.cc
        options = webdriver.ChromeOptions()

        options.add_argument('allow-running-insecure-content')
        options.add_argument('ignore-certificate-errors')
        options.add_argument('ignore-ssl-errors=yes')

        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "intl": {
                "accept_languages": self.locale
            },
            "profile": {
                "password_manager_enabled": False
            }
        })

        if self.headless:
            options.add_argument('headless')
            options.add_argument(f'window-size={self.window_size}')
        else:
            # Extension can only be installed when not headless
            if self.auth_username and self.auth_password:
                options.add_encoded_extension(self._auth_extension_as_base64(self.auth_username, self.auth_password))

        return options

    def _decorator(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # namespace = inspect.currentframe().f_back.f_locals
            namespace = inspect.stack()[0].frame.f_back.f_locals
            if 'self' not in namespace or not isinstance(namespace['self'], self.__class__):
                p1_args = ', '.join(f'{str(x).strip()}' for x in args)
                p2_args = ', '.join([f'{k}={str(v).strip()}' for k, v in kwargs.items()])
                fn_name = fn.__name__
                fn_arguments = ", ".join(x for x in [p1_args, p2_args] if x)
                self.debug(f'{fn_name}({fn_arguments})')
            return fn(*args, **kwargs)
        return wrapper

    def _firefox_options(self):
        profile = webdriver.FirefoxProfile()
        profile.accept_untrusted_certs = True
        profile.assume_untrusted_cert_issuer = False
        # profile.set_preference(
        #     'network.automatic-ntlm-auth.trusted-uris', '.companyname.com')
        profile.set_preference('intl.accept_languages', self.locale)

        options = webdriver.FirefoxOptions()
        options.profile = profile

        if self.headless:
            options.add_argument('--headless')

        return options

    def _format_locale(self, locale):
        locale = locale.replace('_', '-')
        pattern = r'(-[a-zA-Z]{2})$'

        if self.browser == 'firefox':
            return re.sub(pattern, lambda m: m.group().lower(), locale)

        return re.sub(pattern, lambda m: m.group().upper(), locale)

    def _get_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        ch = logging.StreamHandler()
        ch.setLevel(self.log_level)

        formatter = logging.Formatter(
            f'{" " * self.log_indent}%(asctime)s.%(msecs)03d> %(message)s', datefmt=r'%Y-%m-%d %H:%M:%S')

        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    def _get_webdriver(self):
        browsers = ('chrome', 'edge', 'firefox', 'ie', 'safari')
        config = {'path': os.getcwd(), 'log_level': 50}

        if self.browser not in browsers:
            raise WebDriverException(f'Browser must be one of {browsers}: {self.browser}')

        if self.browser == 'chrome':
            return webdriver.Chrome(
                executable_path=ChromeDriverManager(**config).install(), options=self._chrome_options())
        elif self.browser == 'edge':
            return webdriver.Edge(EdgeChromiumDriverManager(**config).install())
        elif self.browser == 'firefox':
            return webdriver.Firefox(
                executable_path=GeckoDriverManager(**config).install(), options=self._firefox_options(), service_log_path=os.path.devnull)
        elif self.browser == 'ie':
            return webdriver.Ie(executable_path=IEDriverManager(**config).install(), options=self._ie_options())
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

    def _is_clicked(self, locator, scroll_into_view=False, behavior='auto'):
        try:
            element = self.find_element(locator)
            if scroll_into_view:
                element.scroll_into_view(behavior=behavior)
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

    def _is_page_changed_after_refresh(self, body_text_diff=True):
        before_page = self.find_element('//body').text_content if body_text_diff else self.page_source
        self.refresh()
        self.wait_until_page_loaded()
        after_page = self.find_element('//body').text_content if body_text_diff else self.page_source
        return before_page != after_page

    def _is_selectable(self, locator):
        select = self.find_element(locator)

        if select.tag_name != 'select':
            raise WebDriverException(f'Locator is not a select element: {locator}')

        if not select.is_enabled():
            return False

        try:
            options = select.find_elements('css=option')
            return select if len(options) > 0 else False
        except (NoSuchWindowException, StaleElementReferenceException):
            return False

    def _multiple_select_to_be(self, element, state):
        if not isinstance(element, WebElement):
            raise WebDriverException(f'Not WebElement: {element}')

        if element.tag_name != 'select':
            raise WebDriverException(f'Element is not a select: {element}')

        if element.get_attribute('multiple'):
            for option in element.find_elements('css=option'):
                if option.is_selected() != state:
                    option.click()
        else:
            raise WebDriverException(
                f'Element is not a multiple select: {element}')

    def _parse_locator(self, locator):
        how, what = Utils.parse_locator(locator)

        if how == 'yml':
            if self.yml:
                return Utils.parse_locator(self.t(what))
            else:
                raise WebDriverException(
                    'Cannot use "yml=" as locator strategy when the instance is not assigned with .yml file.')

        return how, what

    def _random_option(self, options, ignored_options=[None, "", "0"]):
        option = random.choice(options)

        if option.value in ignored_options:
            options.remove(option)

            if len(options) > 0:
                return self._random_option(options, ignored_options=ignored_options)

            return None

        return option

    def __getattribute__(self, fn_name):
        log_level = object.__getattribute__(self, 'log_level')
        fn_method = object.__getattribute__(self, fn_name)
        if logging.DEBUG >= log_level and not fn_name.startswith('_') and fn_name not in ['debug', 'info', 't'] and hasattr(fn_method, '__self__'):
            decorator = object.__getattribute__(self, '_decorator')
            return decorator(fn_method)
        return fn_method


class SpydrElement(WebElement):
    """Wrap WebElement with Spydr-specific implementations.

    Goals:
        - Add additional functionality to WebElement
        - Provide Spydr locator formats (Utils.parse_locator) to WebElement

    Args:
        spydr_or_element_self (Spydr/SpydrElement): Spydr or SpydrElement self
        element (WebElement): WebElement instance
    """
    def __new__(cls, spydr_or_element_self, element):
        instance = super().__new__(cls)
        instance.__dict__.update(element.__dict__)
        return instance

    def __init__(self, spydr_or_element_self, element):
        if isinstance(spydr_or_element_self, Spydr):
            self.spydr = spydr_or_element_self
        elif isinstance(spydr_or_element_self, WebElement):
            self.spydr = spydr_or_element_self.spydr

    def add_class(self, class_name):
        """Add the given CSS class to the element.

        Args:
            class_name (str): CSS class name
        """
        self.parent.execute_script('return arguments[0].classList.add(arguments[1]);', self, class_name)

    def blur(self):
        """Trigger blur event on the element."""
        self.parent.execute_script('arguments[0].blur();', self)

    @property
    @_WebElementSpydrify()
    def children(self):
        """Get the children elements.

        Returns:
            list[WebElement]: The children elements of the current element.
        """
        return self.parent.execute_script('return arguments[0].children;', self)

    def clear(self):
        """Clears the text if it’s a text-entry element."""
        super().clear()

    def clear_and_send_keys(self, *keys, blur=False, wait_until_enabled=False):
        """Clear the element and then send the given keys.

        Args:
            *keys: Any combinations of strings

        Keyword Arguments:
            blur (bool): Lose focus after sending keys. Defaults to False.
            wait_until_enabled (bool): Whether to wait until the element `is_enabled()` before clearing and sending keys. Defaults to False.

        Returns:
            WebElement: WebElement
        """
        if wait_until_enabled:
            self.spydr.wait_until_enabled(self)

        self.clear()
        self.send_keys(*keys, blur=blur)
        return self

    def click(self, scroll_into_view=False):
        """Click the element.

        Keyword Arguments:
            scroll_into_view (bool): Whether to scroll the element into view before clicking. Defaults to False.
        """
        if scroll_into_view:
            self.scroll_into_view()
        super().click()

    def css_property(self, name):
        """The value of CSS property.

        Args:
            name (str): CSS property name

        Returns:
            str: CSS property value
        """
        return self.value_of_css_property(name)

    @property
    def current_url(self):
        """The element's current URL.

        Returns:
            str: URL
        """
        return self.parent.current_url

    @_WebElementSpydrify()
    def find_element(self, locator):
        """Find the element by the given locator.

        Args:
            locator (str): The locator to identify the element

        Returns:
            WebElement: The element found
        """
        how, what = Utils.parse_locator(locator)
        return self._execute(Command.FIND_CHILD_ELEMENT, {"using": how, "value": what})['value']

    @_WebElementSpydrify()
    def find_elements(self, locator):
        """Find all elements by the given locator.

        Args:
            locator (str): The locator to identify the elements

        Returns:
            list[WebElement]: All elements found
        """
        how, what = Utils.parse_locator(locator)
        return self._execute(Command.FIND_CHILD_ELEMENTS, {"using": how, "value": what})['value']

    @property
    @_WebElementSpydrify()
    def first_child(self):
        """Get the first child element.

        Returns:
            WebElement: The first child element of the current element.
        """
        return self.parent.execute_script('return arguments[0].firstElementChild;', self)

    def focus(self):
        """Trigger focus event on the element."""
        self.parent.execute_script('arguments[0].focus();', self)

    def get_attribute(self, name):
        """Get the given attribute or property of the element.

        Args:
            name (str): Attribute name
        """
        return super().get_attribute(name)

    def get_property(self, name):
        """Get the given property of the element.

        Args:
            name (str): Property name
        """
        return super().get_property(name)

    def has_attribute(self, attribute):
        """Check if the element has the given attribute.

        Args:
            attribute (str): Attribute name

        Returns:
            bool: Whether the attribute exists
        """
        return self.parent.execute_script('return arguments[0].hasAttribute(arguments[1]);', self, attribute)

    def has_class(self, class_name):
        """Check if the element has the given CSS class.

        Args:
            class_name (str): CSS class name

        Returns:
            bool: Whether the CSS class exists
        """
        return self.parent.execute_script('return arguments[0].classList.contains(arguments[1]);', self, class_name)

    def hide(self, locator):
        """Hide the element."""
        self.parent.execute_script('arguments[0].style.display = "none";', self)

    def highlight(self, hex_color='#ff3'):
        """Highlight the element with the given color.

        Args:
            hex_color (str, optional): Hex color. Defaults to '#ff3'.
        """
        self.parent.execute_script('arguments[0].style.backgroundColor = `${arguments[1]}`;', self, hex_color)

    @property
    def html(self):
        """The element's `innerHTML`.

        Returns:
            str: innerHTML
        """
        return self.get_attribute('innerHTML')

    @property
    def html_id(self):
        """The ID of the element.

        Returns:
            str: Element's ID
        """
        return self.get_attribute('id')

    @property
    def id(self):
        """Internal ID used by selenium.

        Returns:
            str: Internal WebElement ID
        """
        return super().id

    def is_displayed(self):
        """Whether the element is visible to a user.

        Returns:
            bool: Whether the element is visible
        """
        return super().is_displayed()

    def is_enabled(self):
        """whether the element is enabled.

        Returns:
            bool: Whether the element is enabled
        """
        return super().is_enabled()

    def is_selected(self):
        """Whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.

        Returns:
            bool: Whether the element is selected
        """
        return super().is_selected()

    @property
    @_WebElementSpydrify()
    def last_child(self):
        """Get the last child element.

        Returns:
            WebElement: The last child element of the current element.
        """
        return self.parent.execute_script('return arguments[0].lastElementChild;', self)

    @property
    def location(self):
        """The location of the element in the renderable canvas.

        Returns:
            dict: The coordonate of the element as dict: {'x': 0, 'y': 0}
        """
        return super().location

    @property
    @_WebElementSpydrify()
    def next_element(self):
        """Get the next element.

        Returns:
            WebElement: The next element of the current element.
        """
        return self.parent.execute_script('return arguments[0].nextElementSibling;', self)

    @property
    @_WebElementSpydrify()
    def parent_element(self):
        """Get the parent element.

        Returns:
            WebElement: The parent element of the current element.
        """
        return self.parent.execute_script('return arguments[0].parentElement;', self)

    @property
    @_WebElementSpydrify()
    def previous_element(self):
        """Get the previous element.

        Returns:
            WebElement: The previous element of the current element.
        """
        return self.parent.execute_script('return arguments[0].previousElementSibling;', self)

    @property
    def rect(self):
        """A dictionary with the size and location of the element.

        Returns:
            dict: The size and location of the element as dict: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        """
        return super().rect

    def right_click(self):
        """Right-click on the element."""
        self.spydr.actions().move_to_element(self).context_click().perform()

    def remove_attribute(self, attribute):
        """Remove the given attribute from the element.

        Args:
            attribute (str): Attribute name
        """
        self.parent.execute_script('''
            var element = arguments[0];
            var attributeName = arguments[1];
            if (element.hasAttribute(attributeName)) {
                element.removeAttribute(attributeName);
            }
        ''', self, attribute)

    def remove_class(self, class_name):
        """Remove the given CSS class to the element.

        Args:
            class_name (str): CSS class name
        """
        self.parent.execute_script('return arguments[0].classList.remove(arguments[1]);', self, class_name)

    def save_screenshot(self, filename):
        """Save a screenshot of the element to filename (PNG).

        Default directory for saved screenshots is defined in: screen_root.

        Args:
            filename (str): Filename of the screenshot

        Returns:
            bool: Whether the file is saved
        """
        return self.screenshot(Utils.to_abspath(filename, suffix='.png', root=self.spydr.screen_root))

    def scroll_into_view(self, behavior="auto", block="start", inline="nearest"):
        """Scroll the element's parent to be displayed.

        Keyword Arguments:
            behavior (str): Defines the transition animation. One of `auto` or `smooth`. Defaults to 'auto'.
            block (str): Defines vertical alignment. One of `start`, `center`, `end`, or `nearest`. Defaults to 'start'.
            inline (str): Defines horizontal alignment. One of `start`, `center`, `end`, or `nearest`. Defaults to 'nearest'.
        """
        behaviors = ('auto', 'smooth')
        positions = ('start', 'center', 'end', 'nearest')

        if self.spydr.browser in ('ie', 'safari'):
            align_to_top = False if block == 'end' else True
            self.parent.execute_script('arguments[0].scrollIntoView(arguments[1]);', self, align_to_top)
        else:
            if behavior not in behaviors:
                raise WebDriverException(f'Behavior is not one of {behaviors}: {behavior}')
            if block not in positions:
                raise WebDriverException(f'Block is not one of {positions}: {block}')
            if inline not in positions:
                raise WebDriverException(f'Inline is not one of {positions}: {inline}')

            self.parent.execute_script(
                'arguments[0].scrollIntoView({ behavior: arguments[1], block: arguments[2], inline: arguments[3] });',
                self, behavior, block, inline)

    def scroll_to(self, x, y):
        """Scroll the elment to the given x- and y-coordinates. (IE not supported)

        Args:
            x (int): x-coordinate
            y (int): y-coordinate
        """
        self.parent.execute_script('arguments[0].scrollTo(arguments[1], arguments[2]);', self, int(x), int(y))

    @_WebElementSpydrify()
    def selectedOptions(self):
        """Get select element's `selectedOptions`.

        Raises:
            WebDriverException: Raise an error if the element is not a select element.

        Returns:
            list[WebElement]: All selected options
        """
        if self.tag_name == 'select':
            return self.get_property('selectedOptions')
        else:
            raise WebDriverException(f'WebElement is not a select: {self}')

    def send_keys(self, *keys, blur=False, wait_until_enabled=False):
        """Simulate typing into the element.

        Args:
            *keys: Any combinations of strings

        Keyword Arguments:
            blur (bool): Lose focus after sending keys. Defaults to False.
            wait_until_enabled (bool): Whether to wait until the element `is_enabled()` before sending keys. Defaults to False.
        """
        if wait_until_enabled:
            self.spydr.wait_until_enabled(self)

        super().send_keys(*keys)

        if blur:
            self.blur()

    def set_attribute(self, attribute, value):
        """Set the given value to the attribute of the element.

        Args:
            attribute (str): Attribute name
            value (str): Attribute name
        """
        self.parent.execute_script('''
            var element = arguments[0];
            var attribute = arguments[1];
            var value = arguments[2];
            element.setAttribute(attribute, value);
        ''', self, attribute, value)

    def show(self):
        """Show the element."""
        self.parent.execute_script('arguments[0].style.display = "";', self)

    @property
    def size(self):
        """The size of the element.

        Returns:
            dict: The size of the element as dict: {'width': 100, 'height': 100}
        """
        return super().size

    def submit(self):
        """Submit a form."""
        super().submit()

    @property
    def tag_name(self):
        """Get the element's tagName.

        Returns:
            str: tagName
        """
        return super().tag_name

    @property
    def text(self):
        """The the element's text. (Only works when the element is in the viewport)

        Returns:
            str: The text of the element
        """
        return super().text

    @property
    def text_content(self):
        """Get the element's text. (Works whether the element is in the viewport or not)

        Returns:
            str: The text of the element
        """
        return self.parent.execute_script('return arguments[0].textContent;', self)

    @text_content.setter
    def text_content(self, text_):
        self.parent.execute_script('return arguments[0].textContent = `${arguments[1]}`;', self, text_)

    def toggle_attribute(self, name):
        """Toggle a Boolean attribute. (IE not supported)

        Args:
            name ([type]): Attribute name
        """
        self.parent.execute_script('return arguments[0].toggleAttribute(arguments[1]);', self, name)

    def toggle_class(self, class_name):
        """Toggole the given CSS class of the element.

        Args:
            class_name (str): CSS class name
        """
        self.parent.execute_script('return arguments[0].classList.toggle(arguments[1]);', self, class_name)

    def trigger(self, event):
        """Trigger the given event on the element.

        Args:
            event (str): Event name
        """
        self.parent.execute_script('''
            var element = arguments[0];
            var eventName = arguments[1];
            var event = new Event(eventName, {"bubbles": false, "cancelable": false});
            element.dispatchEvent(event);
        ''', self, event)

    @property
    def value(self):
        """Get the value of the element.

        Args:
            typecast: Typecast the value. Defaults to `str`.

        Returns:
            The value, by `typecast`, of the element
        """
        return self.get_property('value')

    def wait_until_displayed(self, timeout=None):
        """Wait until the element is displayed.

        Keyword Args:
            timeout (int, optional): Wait timeout. Defaults to Spydr driver timeout.

        Returns:
            bool: Whether the element is displayed
        """
        return self._wait_until(lambda _: self.is_displayed(), timeout=timeout)

    def wait_until_not_displayed(self, timeout=None):
        """Wait until the element is not displayed.

        Keyword Args:
            timeout (int, optional): Wait timeout. Defaults to Spydr driver timeout.

        Returns:
            bool: Whether the element is not displayed
        """
        return self._wait_until(lambda _: not self.is_displayed(), timeout=timeout)

    def _wait_until(self, method, timeout=None):
        driver = self.spydr.driver
        timeout = int(timeout) if timeout is not None else self.spydr.timeout
        return self.spydr.wait(driver, timeout).until(method)

    def __str__(self):
        return self.get_attribute('outerHTML')
