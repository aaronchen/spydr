import configparser
import json
import os
import re
import yaml

from functools import reduce
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

HOWS = {
    'css': By.CSS_SELECTOR,
    'class': By.CLASS_NAME,
    'id': By.ID,
    'link_text': By.LINK_TEXT,
    'name': By.NAME,
    'partial_link_text': By.PARTIAL_LINK_TEXT,
    'tag_name': By.TAG_NAME,
    'xpath': By.XPATH,
    'yml': 'yml'
}
"""Set of HOW strategies to identify elements."""


class INI:
    """Access INI `key=value` using JSON serialization.

    Args:
        file (str): Ini file
        default_section (str): Default section name.  Defaults to 'Spydr'.
    """

    def __init__(self, file, default_section='Spydr', encoding='utf-8'):
        self.file = file
        self.default_section = default_section
        self.encoding = encoding
        self.config = configparser.ConfigParser()

        self.config.read(self.file, encoding=self.encoding)

        if self.default_section not in self.config.sections():
            self.config[self.default_section] = {}

    @property
    def default_section(self):
        """Default section to get/set key/value.

        Returns:
            str: Default section name
        """
        return self.__section

    @default_section.setter
    def default_section(self, section):
        self.__section = str(section)

    def get_key(self, key, section=None):
        """Get value from the given key.

        Args:
            key (str): Key
            section: INI section.  Defaults to the default section.

        Returns:
            Value (any data type JSON supports)
        """
        key = self._to_key(key)
        section = self._to_section(section)

        if section not in self.config.sections():
            raise WebDriverException(f'Section not found: {section}')

        try:
            return json.loads(self.config[section][key])
        except KeyError:
            return None

    def save(self):
        """Save INI file."""
        with open(self.file, 'w', encoding=self.encoding) as file:
            self.config.write(file)

    def set_key(self, key, value, section=None):
        """Set key/value for INI

        Args:
            key (str): Key
            value: Value (any data type JSON supports)
            section: INI section.  Defaults to the default section.
        """
        key = self._to_key(key)
        section = self._to_section(section)

        if section not in self.config.sections():
            self.config[section] = {}

        self.config[section][key] = json.dumps(value, ensure_ascii=self._is_ascii())

    def _is_ascii(self):
        return self.encoding != 'utf-8'

    def _to_key(self, key):
        return str(key)

    def _to_section(self, section):
        return str(section) if section else self.default_section


class Utils:
    """Utilites for Spydr WebDriver

    Raises:
        WebDriverException: Raise an error when `how=what` can not be parsed
    """
    @staticmethod
    def parse_locator(locator):
        """Parse locator with supported `how=what` strategies

        Args:
            locator (str): The locator using supported `how=what` strategies

        Raises:
            WebDriverException: Raise an error when `how=what` is not supported

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
            # Cannot raise InvalidSelectorException as it is ignored in webdriver.wait_until.
            # Use WebDriverException for now.
            raise WebDriverException(f'Failed to parse locator: {locator}')

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

    @staticmethod
    def to_abspath(filename, suffix=None, root=os.getcwd(), mkdir=True):
        """to_abspath(filename, suffix='.png', root=os.getcwd(), mkdir=True)
        Resolve file to absolute path and create all directories if missing.

        Args:
            filename (str): File name
            suffix (str, optional): File suffix. Defaults to None.
            root (str, optional): Root directory. Defaults to os.getcwd().
            mkdir (bool, optional): Create directores in the path. Defaults to True.

        Returns:
            str: Absolute path of the file
        """
        if suffix and not filename.lower().endswith(suffix):
            filename += suffix

        abspath = os.path.abspath(os.path.join(root, Utils.sanitize(filename)))
        dirname = os.path.dirname(abspath)

        if mkdir and not os.path.exists(dirname):
            os.makedirs(dirname)

        return abspath


class YML:
    """Access YAML configuration file using dot notataion.

    Args:
        file (str/bytes/os.PathLike): YAML file
    """

    def __init__(self, file):
        self.__file = file
        self.__yml = None

        if isinstance(file, (str, bytes, os.PathLike)):
            try:
                self.__yml = yaml.safe_load(open(file, 'r').read())
            except FileNotFoundError:
                raise WebDriverException(f'File not found: {file}')

    @property
    def dict(self):
        """YAML dict.

        Returns:
            dict: YAML dict
        """
        return self.__yml

    def t(self, key, **kwargs):
        """Get value from YAML file by using "dot notation" key.

        Examples:
            | # YAML
            | today:
            |   dashboard:
            |     search: '#search'
            |     name: 'Name is {name}'
            |
            | t('today.dashboard.search') => '#search'
            | t('today.dashboard.name', name='Spydr') => 'Name is Spydr'

        Args:
            key (str): Dot notation key

        Keyword Arguments:
            **kwargs: Format key value (str) with `str.format(**kwargs)`.

        Returns:
            value of dot notation key
        """
        if not self.__yml:
            return None

        try:
            value = reduce(lambda c, k: c[k], key.split('.'), self.__yml)

            if isinstance(value, str) and kwargs:
                for placeholder in kwargs.keys():
                    if not value.find(f'{{placeholder}}'):
                        raise WebDriverException(
                            f'{key} has no placeholder: {placeholder}')
                return value.format(**kwargs)

            return value
        except KeyError:
            raise WebDriverException(f'Key not found: {key}')
