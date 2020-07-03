# spydr
Selenium Webdriver (Python binding) wrapper with Selenium IDE-like functionality

# Install

`pip install spydr`

# How-To

```python
from spydr.webdriver import Spydr

s = Spydr()
s.maximize_window()
s.open('https://www.google.com/')
s.send_keys('name=q', 'webdriver', s.keys.ENTER)
s.save_screenshot('sample_shot')
s.quit()
```
