# spydr
Selenium Webdriver (Python binding) wrapper with Selenium IDE-like functionality

# How-To

```python
from spydr.webdriver import Spydr

sp = Spydr()
sp.maximize_window()
sp.get('https://www.google.com/')
sp.send_keys('name=q', 'webdriver', sp.keys.ENTER)
sp.save_screenshot('sample_shot')
sp.quit()
```
