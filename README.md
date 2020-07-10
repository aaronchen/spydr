# spydr
Selenium WebDriver (Python binding) wrapper with Selenium IDE-like functionality

[spydr Documentation](https://aaronchen.github.io/spydr/source/spydr.html)

# Install

`pip install spydr`

# Using Sypdr WebDriver

``` python
# Basic Example: Google search 'webdriver'
from spydr.webdriver import Spydr

s = Spydr()
s.maximize_window()
s.open('https://www.google.com/')
s.send_keys('name=q', 'webdriver', s.keys.ENTER)
s.save_screenshot('sample_shot')
s.quit()
```

``` python
# Basic Example: Switch frame and window
from spydr.webdriver import Spydr

s = Spydr()
s.maximize_window()
s.log('JSFiddle: Open New Winodw Link')
s.open('https://jsfiddle.net/s7gcx1du/')
s.switch_to_frame('name=result')
s.click('link_text=New Window')
s.switch_to_last_window_handle()
s.save_screenshot('new_window')
s.quit()
```

``` python
# Handle Basic/Digest HTTP AUTH using Chrome
from spydr import webdriver

s = webdriver.Spydr(auth_username='guest', auth_password='guest')
s.open('https://jigsaw.w3.org/HTTP/Basic/')
s.save_screenshot('basic')
s.open('https://jigsaw.w3.org/HTTP/Digest/')
s.save_screenshot('digest')
s.quit()
```

``` python
# Handle Basic/Digest HTTP AUTH using non-Chrome
from spydr import webdriver

s = webdriver.Spydr(browser='firefox', auth_username='guest', auth_password='guest')
s.open_with_auth('https://jigsaw.w3.org/HTTP/Basic/')
s.save_screenshot('basic')
s.open_with_auth('https://jigsaw.w3.org/HTTP/Digest/')
s.save_screenshot('digest')
s.quit()
```

# Supported **_locator_**

**_Format: 'how=what'_**

- `css=.btn`
- `class=btn-primary`
- `id=frame1`
- `link_text=text`
- `name=j_username`
- `partial_link_text=text`
- `tag_name=span`
- `xpath=//span/a`

If **_how_** is not specified, locator starting with `/` or `(` will be parsed as **xpath**, while `.`, `[` and `#` are treated as **css**.

**css** pseudo selector support => `:eq()`


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
sphinx\make html
```

# Upload Package

```
cd spydr
python setup.py bdist_wheel
twine upload dist\*
```

# Project Home

[https://pypi.org/project/spydr/](https://pypi.org/project/spydr/)