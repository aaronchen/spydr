# spydr
Selenium Python WebDriver Wrapper - Commonly used WebDriver functionality in a package.

[spydr WebDriver - Spydr documentation](https://aaronchen.github.io/spydr/source/spydr.html#spydr.webdriver.Spydr)

[spydr WebElement - SpydrElement documentation](https://aaronchen.github.io/spydr/source/spydr.html#spydr.webdriver.SpydrElement)

# Install

`pip install spydr`

# Supported **_locator_**

Spydr WebDriver supports **_locator_** using the following `how=what` strategies to locate elements:

- `css=.btn`
- `class=btn-primary`
- `id=frame1`
- `link_text=Click here`
- `name=j_username`
- `partial_link_text=Go to`
- `tag_name=span`
- `text=Save As Draft`
- `xpath=//span/a`
- `yml=today_page.dashboard.search_field`

If **_how_** is not specified, **_locator_** starting with `/` or `(` will be parsed as **xpath**, while `.`, `[` and `#` are treated as **css**.

**_locator_** also supports **css** pseudo selector `:eq()`, like using `.tab:eq(2)` to locate 3rd element of `.tab`.

# Using Sypdr WebDriver

``` python
# Basic Example 1:
# - Google search 'webdriver'
from spydr.webdriver import Spydr

s = Spydr()
s.maximize_window()
s.open('https://www.google.com/')
s.send_keys('name=q', 'webdriver', s.keys.ENTER)
s.save_screenshot('sample-1')
s.quit()
```

``` python
# Basic Example 2:
# - Firefox driver, in headless mode, with 1920x1080 resolution
# - Switch frame and window
from spydr.webdriver import Spydr

s = Spydr(browser='firefox', headless=True, log_level='INFO', window_size='1920,1080')
s.info('JSFiddle: Test "Open New Tab/Window"')
s.maximize_window()
s.open('https://jsfiddle.net/s7gcx1du/')
s.switch_to_frame('name=result')
s.click('link_text=New Window', switch_to_new_target=True)
s.save_screenshot(s.timestamp(prefix='sample-'))
s.quit()
```

``` python
# Handle Basic/Digest HTTP AUTH using Chrome
from spydr.webdriver import Spydr

s = Spydr(auth_username='guest', auth_password='guest')
s.open('https://jigsaw.w3.org/HTTP/Basic/')
s.save_screenshot('basic')
s.open('https://jigsaw.w3.org/HTTP/Digest/')
s.save_screenshot('digest')
s.quit()
```

``` python
# Handle Basic/Digest HTTP AUTH using non-Chrome
from spydr.webdriver import Spydr

s = Spydr(browser='firefox', auth_username='guest', auth_password='guest')
s.open_with_auth('https://jigsaw.w3.org/HTTP/Basic/')
s.save_screenshot('basic')
s.open_with_auth('https://jigsaw.w3.org/HTTP/Digest/')
s.save_screenshot('digest')
s.quit()
```

# Using YML: Dot Notation

``` YML
# conf.yml
env:
  url: 'https://dev.company.com/today'

today_page:
  dashboard:
    search_field: '#dashboard-search'
    search_string: 'name is {name}'
```

``` python
from spydr.webdriver import Spydr

s = Spydr(yml='conf.yml')

url = s.t('env.url')
search_string = s.t('today_page.dashboard.search_string', name='spydr')

s.open(url)
s.send_keys('yml=today_page.dashboard.search_field', search_string)  # using yml as locator
```

# Using INI: JSON serialization
``` INI
; conf.ini
[Spydr]
url = "https://www.google.com"
query = "webdriver"
```

``` python
from spydr.webdriver import Spydr

s = Spydr(ini='conf.ini')

url = s.get_ini_key('url')
query = s.get_ini_key('query')

s.open(url)
s.send_keys('name=q', query, s.keys.ENTER)

first_result = s.text('.r > a h3:eq(0)')  # Get first search result
s.set_ini_key('first_result', first_result)  # add first_result to the INI file
all_results = s.texts('.r > a h3') # Get all results
s.set_ini_key('all_results', all_results)  # add all results to the INI file
s.save_ini()  # Save the INI file

s.quit()
```

# SpydrElement (WebElement with Spydr functionality)

``` python
from spydr.webdriver import Spydr

s = Spydr()

# ...

table = s.find_element('#table')

td = table.find_element('css=td[data-id="12345"]')

if td.parent_element.last_child.text == 'complete':
    td.next_element.find_element('.comment').send_keys('Comment here', blur=True)
else:
    td.parent_element.first_child.find_element('css=a.update').click()
```

# Development Environment

```
cd spydr
pip install -e .
pip install autopep8
pip install pylint
pip install twine
pip install sphinx
pip install sphinxcontrib-napoleon
```

# Build Docs

```
cd spydr
sphinx/make html
```

# Upload Package

```
cd spydr
python -B setup.py bdist_wheel
twine upload dist/*
```

# Project Home

[https://pypi.org/project/spydr/](https://pypi.org/project/spydr/)