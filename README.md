# spydr
Selenium Webdriver (Python binding) wrapper with Selenium IDE-like functionality

# How-To

```python
from spydr.webdriver import Spydr

s = Spydr()
s.maximize_window()
s.get('https://www.google.com/')
s.send_keys('name=q', 'webdriver', sp.keys.ENTER)
s.save_screenshot('sample_shot')
s.quit()
```
