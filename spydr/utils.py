import configparser
import json
import os
import platform
import random
import re
import shutil
import yaml

from datetime import datetime
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
    'text': By.XPATH,
    'xpath': By.XPATH,
    'yml': 'yml'
}
"""Set of HOW strategies to identify elements."""


class INI:
    """Access INI `key=value` using JSON serialization.

    Args:
        file (str): Ini file
        default_section (str): Default section name.  Defaults to 'Spydr'.

    Keyword Arguments:
        encoding (str): File Encoding. Defaults to 'utf-8'.
        interpolation: Value interpolation. Can be BasicInterpolation or ExtendedInterpolation. Defaults to None.
    """

    def __init__(self, file, default_section='Spydr', encoding='utf-8', interpolation=None):
        self.file = file
        self.default_section = default_section
        self.encoding = encoding
        self.config = configparser.ConfigParser(interpolation=interpolation)

        self.config.read(Utils.to_abspath(file), encoding=self.encoding)

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
    """Utilities for Spydr WebDriver

    Raises:
        WebDriverException: Raise an error when `how=what` can not be parsed
    """
    @staticmethod
    def compact(iterable, function=None, sorting=False, unique=False):
        """Filter items, by `function`, in list/set. 

        Args:
            iterable (list/set): Iterable
            function: Function to filter. Defaults to None.

        Keyword Arguments:
            sorting (bool): Whether to sort the returned list.
            unique (bool): Whether to remove duplicates in the returned list

        Returns:
            list: Filtered list

        Examples:
            | compact(['', 'a', '', 'b', 0, None, 1]) => [a', b', 1]
        """
        filtered = filter(function, iterable)
        sort = sorted if sorting else list
        return sort(dict.fromkeys(filtered) if unique else filtered)

    @staticmethod
    def date_sorted(dates, reverse=False, format=r'%m/%d/%Y'):
        """Sort list of date strings.

        Args:
            dates (list): List of date strings

        Keyword Arguments:
            reverse (bool): Reverse the sorting. Defaults to False.
            format (str): Date format. Defaults to '%m/%d/%Y'.

        Returns:
            list: Sorted list of date strings
        """
        return sorted(dates, key=lambda date: Utils.strptime(date, format), reverse=reverse)

    @staticmethod
    def is_file(file_path):
        """Wether the file exists.

        Args:
            file_path (str): File Path

        Returns:
            bool: Wether the file exists
        """
        file = Utils.to_abspath(file_path, mkdir=False)

        return os.path.exists(file)

    @staticmethod
    def remove_dir(dir):
        """Remove the directory.

        Args:
            dir (str): Directory path
        """
        dir = Utils.to_abspath(dir, mkdir=False, isdir=True)

        if os.path.isdir(dir):
            shutil.rmtree(dir, ignore_errors=True)

    @staticmethod
    def remove_file(file):
        """Remove the file.

        Args:
            file (str): File path
        """
        file = Utils.to_abspath(file, mkdir=False)

        if os.path.exists(file):
            os.remove(file)

    @staticmethod
    def same_set(string_1, string_2, sep=r',?\s+'):
        """Check if `string_1` and `string_2` are the same set after being split by `sep`.

        Args:
            string_1 (str): String 1
            string_2 (str): String 2
            sep (regexp, optional): Regex separator. Defaults to r',?\s+'.

        Returns:
            bool: Whether string_1 and string_2 are the same

        Examples:
            | same_set('Bruce Lee', 'Lee, Bruce') => True
            | same_set('Bruce Lee', 'Lee Bruce') => True
        """
        string_1_set = set(re.split(sep, string_1))
        string_2_set = set(re.split(sep, string_2))
        return string_1_set == string_2_set

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
                if somehow == 'text':
                    what = f'//*[contains(text(), "{what}")]'

        if how is None:
            # Cannot raise InvalidSelectorException as it is ignored in webdriver.wait_until.
            # Use WebDriverException for now.
            raise WebDriverException(f'Failed to parse locator: {locator}')

        return how, what

    @staticmethod
    def path_exists(path):
        """Check if path exists.

        Args:
            path (str): Path

        Returns:
            bool: Whether path exists.
        """
        return os.path.exists(Utils.to_abspath(path, mkdir=False))

    @staticmethod
    def random_choice(sequence):
        """Choose a random element from a non-empty sequence.

        Args:
            sequence (Sequence[_T]): Sequence

        Returns:
            _T: A random element in the sequence
        """
        return random.choice(sequence)

    @staticmethod
    def random_sample(population, k):
        """Return a `k` length list of unique elements chosen from the `population` sequence.

        Args:
            population (Sequence[_T]): Sequence
            k (int): Length of the returned list

        Returns:
            List[_T]: Returns a new list containing elements from the population
        """
        return random.sample(population, k)

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
    def strip_multi_spaces(words):
        """Strip multiple spaces between words to be single-spaced.

        Args:
            words (srt): Words

        Returns:
            str: Single-spaced words
        """
        return ' '.join(words.split()).strip()

    @staticmethod
    def strptime(date, format=r'%m/%d/%Y'):
        """Parse date string to `datetime.datetime` object

        Args:
            date (str): Date string
            format (str, optional): Date format. Defaults to r'%m/%d/%Y'.

        Returns:
            datetime.datetime/None: Return datetime.datetime or None if failed to parse date string.
        """
        try:
            return datetime.strptime(date, format)
        except ValueError:
            return None

    @staticmethod
    def to_abspath(path, suffix=None, root=os.getcwd(), mkdir=True, isdir=False):
        """to_abspath(path, suffix='.png', root=os.getcwd(), mkdir=True, isdir=False)
        Resolve file to absolute path and create all directories if missing.

        Args:
            path (str): Path

        Keyword Args:
            suffix (str): File suffix. Defaults to None.
            root (str): Root directory. Defaults to os.getcwd().
            mkdir (bool): Create directores in the path. Defaults to True.
            isdir (bool): Whether path is a directory. Defaults to False.

        Returns:
            str: Absolute path
        """
        if suffix and not path.lower().endswith(suffix):
            path += suffix

        abspath = os.path.abspath(os.path.join(root, path))

        if isdir:
            abspath = os.path.join(abspath, '')

        dirname = os.path.dirname(abspath)

        if mkdir and not os.path.exists(dirname):
            os.makedirs(dirname)

        return abspath

    @staticmethod
    def true(obj):
        """Evaluate object(int/float/str) to Boolean

        Args:
            obj (int/float/str): Object to evaluate

        Returns:
            bool: Whether Object is evaluated to True
        """
        if isinstance(obj, bool):
            return obj
        elif isinstance(obj, (int, float)):
            return obj > 0
        elif isinstance(obj, str):
            return obj.lower() in ['true', 'yes', 't', 'y', '1']
        else:
            return False


class YML:
    """Access YAML configuration file using dot notation.

    Args:
        file (str/bytes/os.PathLike): YAML file
    """

    def __init__(self, file):
        self.__file = file
        self.__yml = None

        if isinstance(file, (str, bytes, os.PathLike)):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self.__yml = yaml.safe_load(f)
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
