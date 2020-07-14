import re

from selenium.common.exceptions import InvalidSelectorException
from selenium.webdriver.common.by import By


HOWS = {
    'css': By.CSS_SELECTOR,
    'class': By.CLASS_NAME,
    'id': By.ID,
    'link_text': By.LINK_TEXT,
    'name': By.NAME,
    'partial_link_text': By.PARTIAL_LINK_TEXT,
    'tag_name': By.TAG_NAME,
    'xpath': By.XPATH
}
"""Set of HOW strategies to identify elements."""


class Utils:
    """Utilites for Spydr WebDriver

    Raises:
        InvalidSelectorException: Raise an error when `how=what` can not be parsed
    """
    @staticmethod
    def parse_locator(locator):
        """Parse locator with supported `how=what` strategies

        Args:
            locator (str): The locator using supported `how=what` strategies

        Raises:
            InvalidSelectorException: Raise an error when `how=what` is not supported

        Returns:
            (str, str): (how, what) strategy
        """
        how = what = None
        matched = re.search('^([A-Za-z_]+)=(.+)', locator)

        if matched is None:
            what = locator
            if locator.startswith(('.', '#', '[')):
                how = HOWS['css']
            elif locator.startswith(('/', '(')):
                how = HOWS['xpath']
        else:
            somehow, what = matched.group(1, 2)
            if somehow in HOWS:
                how = HOWS[somehow]

        if how is None:
            raise InvalidSelectorException(
                f'Failed to parse locator: {locator}')

        return how, what

    @staticmethod
    def sanitize(text):
        """Sanitize text to be safe for file names.

        Args:
            text (str): text to sanitize

        Returns:
            str: sanitized text
        """
        text = str(text).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.\/]', '', text)
