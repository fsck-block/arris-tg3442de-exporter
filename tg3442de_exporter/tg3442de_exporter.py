'''
=head1 NAME
tg3442de_exporter Prometheus Plugin to monitor status of Arris TG3442DE

=head1 DESCRIPTION

=head1 REQUIREMENTS
- BeautifulSoup
- pycryptodome

'''

import json
import logging
import threading
import time
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from typing import Dict
import traceback
import logging

import click
from prometheus_client import CollectorRegistry, MetricsHandler
from prometheus_client.metrics_core import GaugeMetricFamily
from requests import Timeout

from tg3442de_exporter.tg3442de import TG3442DE
from tg3442de_exporter.config import (
    load_config,
    IP_ADDRESS,
    PASSWORD,
    EXPORTER,
    PORT,
    TIMEOUT_SECONDS,
    EXTRACTORS,
    SIMULATE
)


'''
from connectbox_exporter.logger import get_logger, VerboseLogger
'''
from tg3442de_exporter.html2metric import get_metrics_extractor

# Taken 1:1 from prometheus-client==0.7.1, see https://github.com/prometheus/client_python/blob/3cb4c9247f3f08dfbe650b6bdf1f53aa5f6683c1/prometheus_client/exposition.py
class _ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    """Thread per request HTTP server."""

    # Make worker threads "fire and forget". Beginning with Python 3.7 this
    # prevents a memory leak because ``ThreadingMixIn`` starts to gather all
    # non-daemon threads in a list in order to join on them at server close.
    # Enabling daemon threads virtually makes ``_ThreadingSimpleServer`` the
    # same as Python 3.7's ``ThreadingHTTPServer``.
    daemon_threads = True

class TG3442DECollector(object):
    def __init__(
        self,
        logger,
        ip_address: str,
        password: str,
        exporter_config: Dict,
    ):
        self.logger = logger
        self.ip_address = ip_address
        self.password = password
        self.timeout = exporter_config[TIMEOUT_SECONDS]
        self.simulate = (exporter_config[SIMULATE] == 1)

        extractors = exporter_config[EXTRACTORS]
        self.metric_extractors = [get_metrics_extractor(e, logger) for e in extractors]
        #self.logger.debug("TG3442DECollector metric_extractors ="+str(self.metric_extractors))

    def collect(self):
        # Collect scrape duration and scrape success for each extractor. Scrape success is initialized with False for
        # all extractors so that we can report a value for each extractor even in cases where we abort midway through
        # because we lost connection to the modem.
        scrape_duration = {}  # type: Dict[str, float]
        scrape_success = {}
        self.logger.info("Collecting from " + self.ip_address)

        # attempt login
        login_logout_success = True
        try:
            box = TG3442DE(
                self.logger, self.ip_address, key=self.password, timeout=self.timeout, simulate=self.simulate
            )
            box.login()
        except (ConnectionError, Timeout, ValueError) as e:
            self.logger.error(repr(e))
            box = None
            login_logout_success = False

        # skip extracting further metrics if login failed
        if box is not None:
            for extractor in self.metric_extractors:
                self.logger.debug("extractor ="+str(extractor))
                raw_htmls = {}
                try:
                    pre_scrape_time = time.time()

                    # obtain all raw html responses for an extractor, then extract metrics
                    for page in extractor.pages:
                        self.logger.debug(f"Querying page={page}...")
                        raw_html = box.html_getter(page, "")
                        self.logger.debug(
                            f"Raw HTML response for page={page}:\n{raw_html}"
                        )
                        raw_htmls[page] = raw_html
                    yield from extractor.extract(raw_htmls)
                    post_scrape_time = time.time()

                    scrape_duration[extractor.name] = post_scrape_time - pre_scrape_time
                    scrape_success[extractor.name] = True

                except (ValueError, KeyError, AssertionError) as e:
                    stack = traceback.format_exc()
                    message = f"Failed to extract '{extractor.name}'. \n{stack}"
                    self.logger.error(message)
                except (AttributeError) as e:
                    # in case of a less serious error, log and continue scraping the next extractor
                    stack = traceback.format_exc()
                    message = f"Failed to extract '{extractor.name}'. raw_htmls:\n{stack}\n{raw_htmls}"                    
                    self.logger.error(message)
                except (BrokenPipeError,ConnectionError, Timeout) as e:
                    # in case of serious connection issues, abort and do not try the next extractor
                    self.logger.error(repr(e))
                    break



            # attempt logout once done
            try:
                box.logout()
            except Exception as e:
                self.logger.error(e)
                login_logout_success = False
        scrape_success["login_logout"] = int(login_logout_success)

        # create metrics from previously durations and successes collected
        EXTRACTOR = "extractor"
        scrape_duration_metric = GaugeMetricFamily(
            "tg3442de_scrape_duration",
            documentation="Scrape duration by extractor",
            unit="seconds",
            labels=[EXTRACTOR],
        )
        for name, duration in scrape_duration.items():
            scrape_duration_metric.add_metric([name], duration)
        yield scrape_duration_metric

        scrape_success_metric = GaugeMetricFamily(
            "tg3442de_up",
            documentation="TG3442DE exporter scrape success by extractor",
            labels=[EXTRACTOR],
        )
        for name, success in scrape_success.items():
            scrape_success_metric.add_metric([name], int(success))
        yield scrape_success_metric


@click.command()
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False))
@click.option('-d','--debug', is_flag=True, help="show debug messages",)
def main(config_file='config.yml', debug=False):
    """
    Launch the exporter using a YAML config file.
    """

    log_level = logging.DEBUG if debug else logging.INFO
    format1='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    format2='[%(asctime)s:%(levelname)05s:%(filename)20s:%(lineno)3s - %(funcName)25s() ] %(message)s'
    logging.basicConfig(format=format2, level=log_level)
    logger = logging.getLogger()

    # load user and merge with defaults
    config = load_config(config_file)
    exporter_config = config[EXPORTER]
    

    # fire up collector
    reg = CollectorRegistry()
    reg.register(
        TG3442DECollector(
            logger,
            ip_address=config[IP_ADDRESS],
            password=config[PASSWORD],
            exporter_config= config[EXPORTER],
        )
    )

    # start http server
    CustomMetricsHandler = MetricsHandler.factory(reg)
    httpd = _ThreadingSimpleServer(("", exporter_config[PORT]), CustomMetricsHandler)
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.start()

    logger.info(
        f"Exporter running at http://localhost:{exporter_config[PORT]}, querying {config[IP_ADDRESS]}"
    )

    # wait indefinitely
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        httpd.shutdown()
        httpd_thread.join()
