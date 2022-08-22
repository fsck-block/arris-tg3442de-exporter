
import re
from datetime import timedelta
from logging import Logger
from pathlib import Path
from typing import Iterable, Set, Dict

from prometheus_client import Metric

class HtmlMetricsExtractor:

    def __init__(self, name: str, pages: Set, logger: Logger):
        self._name = name
        self._logger = logger
        self._logger.debug("HtmlMetricsExtractor")
        self._logger.debug("name :" + name)

        # create one parser per function
        self._parsers = {}
        for page in pages:
            self._logger.debug("Page :" +page)
            self._parsers[page] = page

    @property
    def name(self):
        """
        Descriptive name for this extractor, to be used in metric labels
        :return:
        """
        self._logger.debug("HtmlMetricsExtractor :" + self._name)
        return self._name

    @property
    def pages(self) -> Iterable[str]:
        """
        TG3442 pages(s) this metrics extractor is working on
        :return:
        """
        self._logger.debug("HtmlMetricsExtractor " + str(self._parsers.keys()))
        return self._parsers.keys()

    def extract(self, raw_htls: Dict[str, bytes]) -> Iterable[Metric]:
        """
        Returns metrics given raw XML responses corresponding to the functions returned in the `functions` property.
        :param raw_htmls:
        :return: metrics iterable
        :raises: lxml.etree.XMLSyntaxError in case a raw XML does not match the expected schema
        """
        self._logger.debug("HtmlMetricsExtractor")
        raise NotImplementedError

    def re_search(self,pattern,text,no,default='Unknown'):
        result = re.search(pattern,text)
        if result != None:
            if len(result.groups()) != no:
                return [default]*(no)
        else:
            return [default]*(no)
        return(result.groups())

