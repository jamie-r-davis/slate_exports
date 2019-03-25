import sys

from loguru import logger
import requests
from selenium.webdriver.chrome.options import Options
from umdriver import UMDriver

import config


class ContextDriver(UMDriver):
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.quit()

logger.remove()
logger.add(sys.stdout, level='INFO', format='<green>{time}</green> <level>{message}</level>')
logger.add('app.log', level='INFO', format='<green>{time}</green> <level>{message}</level>')

def main():
    options = Options()
    options.headless = True
    # init headless webdriver
    with UMDriver(options=options) as d:
        # authenticate with u-m
        d.login(**config.AUTH)
        # visit each env to establish session cookies
        for env in config.SLATE_ENVS:
            d.get(env['host']+'/manage')
            logger.debug(d.current_url)
            # init requests session
            s = requests.session()
            # grab cookies from webdriver session
            for cookie in d.get_cookies():
                s.cookies.set(cookie['name'], cookie['value'])
            query_url = '{host}{endpoint}'
            r = s.get(query_url.format(**env))
            logger.debug(r.json())
            for q in r.json()['row']:
                export_url = '{host}/manage/service/export?id={id}'
                r2 = s.get(export_url.format(host=env['host'], id=q['id']))
                logger.info(f"[{env['host']}] {r2.status_code}: {r2.text} ({q['name']})")

if __name__ == '__main__':
    main()
