import sys
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
import requests
from selenium.webdriver.chrome.options import Options
from umdriver import UMDriver

import config


logger.remove()
logger.add(sys.stdout, level='INFO', format='<green>{time}</green> <level>{message}</level>')
logger.add('app.log', level='DEBUG', format='<green>{time}</green> <level>{message}</level>')


def run_query(session, host, query, name='Unnamed Query'):
    logger.info(f"[{host}] - {name} ({query})")
    # url = f"{host}/manage/query/query?id={query}"
    url = f"{host}/manage/service/export?id={query}"
    r = session.get(url)
    if r.status_code == 200:
        logger.info(f"{r.status_code} {r.text}")
    else:
        logger.error(f"{r.status_code} {r.text}")

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
                with ThreadPoolExecutor(max_workers=4) as executor:
                    for q in r.json()['row']:
                        executor.submit(run_query, s, env['host'], q['id'], q['name'])
        # fire any one-off queries
        if '--one-offs' in sys.argv:
            logger.info('Running one-off queries...')
            for q in config.ONE_OFF_QUERIES:
                # make sure driver has session
                d.get(f"{q['host']}/manage")
                # create clean session with cookies from driver
                s = requests.session()
                get_cookies(d, s)
                # run query
                run_query(s, **q)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logger.error('Please provide command line arguments [--integrations | --one-offs]')
    else:
        main()
