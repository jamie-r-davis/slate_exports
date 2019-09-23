import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from loguru import logger

import config

logger.remove()
logger.add(
    sys.stdout, level="INFO", format="<green>{time}</green> <level>{message}</level>"
)


def get_external_session(hostname, username, password):
    """Returns an authenticated session for an external user.

    Parameters
    ----------
    hostname : str
        The hostname of the slate environment to use, including protocol (eg, https://slateuniversity.net)
    username : str
        The username to use for authentication
    password : str
        The password to use for authentication
    """
    url = f"{hostname}/manage/login?cmd=external"
    s = requests.session()
    r1 = s.get(url)
    s.headers.update({"Origin": hostname})
    r2 = s.post(r1.url, data={"user": username, "password": password})
    r2.raise_for_status()
    return s


def run_query(session, host, query, name="Unnamed Query"):
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
        session.cookies.set(cookie["name"], cookie["value"])


def notify_slack(webhook, message):
    requests.post(
        webhook, json={"text": message}, headers={"Conternt-type": "application/json"}
    )


def main():
    username = os.environ.get("SLATE_EXPORTS_USER")
    password = os.environ.get("SLATE_EXPORTS_PASSWORD")
    SLACK_WEBHOOK = os.environ.get("SLATE_EXPORTS_SLACK_WEBHOOK")

    # visit each env to establish session cookies
    if "--integrations" in sys.argv:
        logger.info("Running integration queries...")
        for env in config.SLATE_ENVS:
            s = get_external_session(env["host"], username, password)
            # grab cookies from webdriver session
            query_url = "{host}{endpoint}"
            r = s.get(query_url.format(**env))
            logger.debug(r.json())
            with ThreadPoolExecutor(max_workers=4) as executor:
                for q in r.json()["row"]:
                    if q["active"] == "1":  # only execute active queries
                        executor.submit(run_query, s, env["host"], q["id"], q["name"])
            if SLACK_WEBHOOK:
                notify_slack(
                    SLACK_WEBHOOK, f'`{env["host"]}`: Integration exports finished'
                )

    # fire any one-off queries
    if "--one-offs" in sys.argv:
        logger.info("Running one-off queries...")
        for q in config.ONE_OFF_QUERIES:
            # initialize session
            s = get_external_session(q["host"], username, password)
            # run query
            run_query(s, **q)

    # force import/pickup
    if "--imports" in sys.argv:
        logger.info("Running imports...")
        for host in config.IMPORT_HOSTS:
            s = get_external_session(host, username, password)
            r = s.get(f"{host}/manage/service/import?cmd=pickup")
            r.raise_for_status()
            logger.info(r.text)
            try:
                r2 = s.get(f"{host}/manage/import/load?cmd=process", timeout=10)
            except requests.exceptions.ReadTimeout:
                logger.debug("Import request sent, connection closed.")
            else:
                logger.info(r2.text)
            finally:
                if SLACK_WEBHOOK:
                    notify_slack(
                        SLACK_WEBHOOK, f"`{host}`: Force pickup/import completed"
                    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error(
            "Please provide command line arguments [--integrations | --one-offs | --imports]"
        )
    else:
        main()
