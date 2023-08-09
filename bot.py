#!/usr/bin/env python3

import sys
import traceback
import json
import requests
import logging
from termcolor import colored
# from bs4 import BeautifulSoup
import click
import click_completion
from subprocess import call


logger = logging.getLogger(__name__)
click_completion.init()
STATUS_TYPES = {
    "performing-draft": "Performing-20Draft",
    "initial-draft": "Initial-20Draft",
    "initial-review": "Initial-20Review",
    "performing-review": "Performing-20Review",
    "final": "Final",
    "withdrawn": "Withdrawn"
               }

ADDITIONAL_OBJECTS = {
    "status": "Test case status=Status",
    "standards": "Is testing=Standards",
    "keywords": "Keyword=Keywords",
    "providers": "Is provided by=Providers",
    "consumers": "Is consumed by=Consumers",
    "objectives": "Focus area objectives",
    "purpose": "Description=Purpose",
    "pre-condition": "Precondition=Pre-condition",
    "validation-criteria": "Validation criteria",
    "result": "Test result=Result"
                     }


def tcparser(session, jsondata, limit, capability, browser, browseredit):
    red = []
    green = []
    testcases = [key for key, val in jsondata['results'].items()]
    for testcase in testcases:
        limit = limit - 1
        if limit < 0:
            return
        uri = f"{URL}?title=Test%20Case%20Validation&pageContext={testcase}"
        rawdata = session.get(uri)
        # soup = BeautifulSoup(rawdata.text)
        if f'CC-{capability}' in rawdata.text:
            red.append(testcase)
            print(colored(uri, 'red'))
            if browser:
                browseruri = f"{URL}?title={testcase}"
                if browseredit:
                    browseruri += "&action=formedit"
                call(["xdg-open", browseruri])

            elif browseredit:
                browseruri = f"{URL}?title={testcase}&action=formedit"
                call(["xdg-open", browseruri])

        else:
            green.append(testcase)
            print(colored(uri, 'green'))


def flattenjson(jsondata):
    with open('data.json', 'w') as outfile:
        json.dump(jsondata, outfile)
    data = []
    for key, values in jsondata['results'].items():
        consumers = [
            consumer['fulltext']
            for consumer in values['printouts']['Consumers']
        ]
        data.append({"name": key, "consumers": consumers})
    with open('static/consumed.json', 'w') as outfile:
        json.dump({"data": data}, outfile)


def search(session, objective, consumed, limit, status, provided, capability, additional_objects):
    base = 'title=Special:Ask'
    search_base = '[[Category:Test Cases]]'

    if consumed:
        search_consumer = f' [[Is consumed by::~*CC-{capability}*]]'
    if provided:
        search_consumer = f' [[Is provided by::~*CC-{capability}*]]'
    if consumed and provided:
        search_consumer = ' [[Is consumed by::~*CC-{0}*]] [[Is provided by::~*CC-{0}*]]'.format(capability)
    logger.debug(search_consumer)

    unqoute_search = search_base
    if status:
        search_status = f' [[Test case status::{status}]]'
        unqoute_search += search_status
    try:
        unqoute_search += search_consumer
    except NameError:
        pass
    if objective:
        search_objective = f' [[Focus area objectives::~*Objective {objective} @ FMNCS Focus Area*]]'
        unqoute_search += search_objective

    if additional_objects:
        additional_string = '&po='
        for obj in additional_objects:
            additional_string += f'?{obj}%0D'
        unqoute_search += additional_string

    unqoute_search += '&p[format]=json&p[mainlabel]=TC'

    uri = f"{URL}?{base}&q={unqoute_search}"

    logger.info(uri)
    rawdata = session.get(uri)
    try:
        return rawdata.json()
    except ValueError:
        logger.error(colored("Empty Resultset Returned", 'red'))
        return None
    except Exception:
        traceback.print_exc()
        logger.debug(rawdata.text)


class Session(object):
    def __init__(self, host, user, password):
        path = "Main_Page"
        s = requests.Session()
        s.auth = (user, password)
        login = s.get(f'{host}/{path}')
        self.session = s
        logger.debug(login.cookies)


@click.group(invoke_without_command=True)
@click.option('--user', prompt='Username')
@click.option('--password', prompt='Password')
@click.option('--host', prompt='Host')
@click.option('--debug', is_flag=True)
@click.option('--objective', '-o', type=click.IntRange(2, 12))
@click.option('--consumed', is_flag=True)
@click.option('--provided', is_flag=True)
@click.option('--limit', default=1000)
@click.option('--status', default="performing-draft", type=click.Choice(STATUS_TYPES.keys()))
@click.option('--additional', multiple=True, type=click.Choice(ADDITIONAL_OBJECTS.keys()))
@click.option('--capability', default="321")
@click.pass_context
def init(ctx, user, password, host, debug, objective, consumed, provided, status, limit, capability, additional):
    handler = logging.StreamHandler(sys.stdout)
    level = logging.DEBUG if debug else logging.INFO

    global URL
    URL = host

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=[handler]
    )

    if not consumed and not provided:
        logger.error("Either set '--consumed' OR '--provided':")
        return
    session = Session(host, user, password)

    additional_real = [val for key, val in ADDITIONAL_OBJECTS.items() if key in additional]
    status_real = STATUS_TYPES[status]

    jsondata = search(session.session, objective, consumed, limit,
                      status_real, provided, capability, additional_real)
    if jsondata is not None:
        ctx.obj = [session.session, jsondata, limit, capability]
        if ctx.invoked_subcommand is None:
            ctx.invoke(validate)


@init.command()
@click.option('--browser', help="Open undone Testcases", is_flag=True)
@click.option('--browseredit', is_flag=True)
@click.pass_obj
def validate(ctxobj, browser, browseredit):
    """Validate Testcases and open in Browser"""

    if ctxobj is None:
        return

    session, jsondata, limit, capability = ctxobj
    tcparser(session, jsondata, limit, capability, browser, browseredit)


@init.command()
@click.pass_obj
def dump(ctxobj):
    if ctxobj is None:
        return
    _, jsondata, _, _ = ctxobj
    flattenjson(jsondata)


if __name__ == '__main__':
    init(auto_envvar_prefix='BOT')
