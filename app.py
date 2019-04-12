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


def run_query(session, host, query, name='Unnamed Query'):
    url = f"{host}/manage/query/query?id={query}"
    r = session.post(url, data={'cmd': 'run'})
    logger.info(f"[{host}] {r.status_code}: {query} ({name})")

def get_cookies(driver, session):
    """Sets cookies from the driver to the session object"""
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])


def main():
    options = Options()
    options.headless = True
    # init headless webdriver
    with UMDriver(options=options) as d:
        # authenticate with u-m
        d.login(**config.AUTH)
        # visit each env to establish session cookies
        if '--integrations' in sys.argv:
            logger.info('Running integration queries...')
            for env in config.SLATE_ENVS:
                d.get(env['host']+'/manage')
                logger.debug(d.current_url)
                # init requests session
                s = requests.session()
                # grab cookies from webdriver session
                get_cookies(d, s)
                query_url = '{host}{endpoint}'
                r = s.get(query_url.format(**env))
                logger.debug(r.json())
                for q in r.json()['row']:
                    run_query(s, host=env['host'], query=q['id'], name=q['name'])
        # fire any one-off queries
        if '--one-offs' in sys.argv:
            logger.info('Running one-off queries...')
            for query_obj in config.ONE_OFF_QUERIES:
                # make sure driver has session
                d.get(f"{q['host']}/manage")
                # create clean session with cookies from driver
                s = requests.session()
                get_cookies(d, s)
                # run query
                run_query(s, **query_obj)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logger.error('Please provide command line arguments [--integrations | --one-offs]')
    else:
        main()
