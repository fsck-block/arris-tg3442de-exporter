from asyncio.log import logger
from logging import Logger
from typing import Iterable, Set, Dict
import json
from datetime import datetime, timedelta

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor

from prometheus_client import Metric
from prometheus_client.metrics_core import (
    GaugeMetricFamily,
)

CALL_LOG = 'call_log'
GET_CALL_LOG = '/php/phone_call_log_data.php?{%22PhoneLogRecord%22:{}}'


class CallLogExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger, exporter_config: Dict):
        super(CallLogExtractor, self).__init__(
            CALL_LOG, {GET_CALL_LOG}, logger
        )
        self.logger = logger

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("CallLogExtractor")

        # parse Call Log
        raw_html = raw_htmls[GET_CALL_LOG]
        if len(raw_html) < 10:
            return

        # parse json
        json_phone_log_dat = json.loads(raw_html)

        phone_log_record = json_phone_log_dat['PhoneLogRecord']
        no_entries = len(phone_log_record)
        if no_entries == 0:
            return

        last_log_entry = phone_log_record[0]
        # change of day seems to be UTC based
        if last_log_entry['Date'] == "PAGE_CALL_LOG_TABLE_TODAY":
            last_log_entry['Date'] = datetime.strftime(datetime.utcnow(), '%Y-%m-%d')            
        elif last_log_entry['Date'] == "PAGE_CALL_LOG_TABLE_YESTERDAY":
            last_log_entry['Date'] = datetime.strftime(datetime.utcnow() - timedelta(1), '%Y-%m-%d')            
        #last_log_entry['ParameterIndex'] = str(last_log_entry['ParameterIndex'])


        # Store call log entry in label information
        # Not so good idea because prometheus is not a logging system
        labels = ["CallType","Date","Time","ExternalNumber","Duration"]
        call_log = GaugeMetricFamily(
            'tg3442de_call_log',
            'Call log information',
            labels=labels,
        )
        label_values = [last_log_entry[key] for key in labels]
        call_log.add_metric(label_values,float(last_log_entry['ParameterIndex']))
        yield call_log
