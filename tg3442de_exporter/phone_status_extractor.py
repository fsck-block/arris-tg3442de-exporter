from logging import Logger
from typing import Iterable, Set, Dict

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor

from prometheus_client import Metric
from prometheus_client.metrics_core import (
    InfoMetricFamily,
)


PHONE_STATUS   = 'phone_status'
GET_STATUS_PHONE = '/php/status_voice_data.php'

class PhoneStatusExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger, exporter_config: Dict):
        super(PhoneStatusExtractor, self).__init__(
            PHONE_STATUS, {GET_STATUS_PHONE}, logger
        )
        self.logger = logger
        self.vars = {
            "telf_{}_number"     : r".*var js_TELF{}_Number = '(.*)';.*",
            "telf_{}_call_state" : r".*var js_TELF{}_CallPState = '(.*)';.*",
            "telf_{}_hook_state" : r".*var js_TELF{}_HookState = '(.*)';.*",
        }

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("PhoneStatusExtractor")

        # parse GlobalSettings
        raw_html = raw_htmls[GET_STATUS_PHONE]
        if len(raw_html) < 10:
            return

        #var js_NumberOfLine = '2';
        number_of_line = int(self.re_search(r".*var js_NumberOfLine = '(.*)';.*",raw_html,1,0)[0])
        self.logger.debug("number_of_line :" + str(number_of_line))

        values = { 
            'number_of_line' :  str(number_of_line) 
        }

        for line_no in range(1,number_of_line+1):
            for k, p in self.vars.items():
                values[k.format(line_no)] = self.re_search(p.format(line_no),raw_html,1)[0]

        yield InfoMetricFamily(
            'tg3442de_phone_status',
            'Phone status information',
            value=values,
        )

