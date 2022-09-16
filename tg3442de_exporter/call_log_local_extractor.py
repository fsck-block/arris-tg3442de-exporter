from logging import Logger
from typing import Iterable, Set, Dict
import json
from datetime import datetime, timedelta

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor
from prometheus_client import Metric
from prometheus_client.metrics_core import (
    GaugeMetricFamily,
)


CALL_LOG_LOCAL = 'call_log_local'
GET_CALL_LOG_LOCAL = '/php/phone_call_log_data.php?{%22PhoneLogRecord%22:{}}'


class CallLogLocalExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger, exporter_config: Dict):
        super(CallLogLocalExtractor, self).__init__(
            CALL_LOG_LOCAL, {GET_CALL_LOG_LOCAL}, logger
        )
        self.logger = logger
        self.call_log_filename = exporter_config['call_log_filename']

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("CallLogLocal")

        # parse Call Log
        raw_html = raw_htmls[GET_CALL_LOG_LOCAL]
        if len(raw_html) < 10:
            return

        # parse json
        json_phone_log_dat = json.loads(raw_html)

        phone_log_record = json_phone_log_dat['PhoneLogRecord']
        no_entries = len(phone_log_record)
        if no_entries == 0:
            return

        no_entries_added = 0
        log_entries = {}
        for index in range(no_entries):

            date_format = '%d.%m.%Y' # '%Y-%m-%d'
            log_entry = phone_log_record[index]
            # change of day seems to be UTC based
            if log_entry['Date'] == "PAGE_CALL_LOG_TABLE_TODAY":
                log_entry['Date'] = datetime.strftime(datetime.utcnow(), date_format)            
            elif log_entry['Date'] == "PAGE_CALL_LOG_TABLE_YESTERDAY":
                log_entry['Date'] = datetime.strftime(datetime.utcnow() - timedelta(1), date_format)
            # remove ParameterIndex because this value changes for each new entry
            del log_entry['ParameterIndex'] 
            # add unix timestamp for sorting
            dt = "{}-{}".format(log_entry['Date'], log_entry['Time'])
            key = datetime.strptime(dt,'%d.%m.%Y-%H:%M').timestamp()
            log_entries[str(key)] = log_entry

        # TODO: For large call logs work on files directly and not in memory
        # read stored call log
        old_log_entries = {}
        try:
            with open(self.call_log_filename,'r') as in_file: 
              old_log_entries = json.load(in_file)
        except IOError as e:
            self.logger.info("Cannot read old call_log :" +str(e))

        # merge entries
        no_old_entries = len(old_log_entries)
        old_log_entries.update(log_entries)
        no_entries_added = len(old_log_entries) - no_old_entries
          
        # save call log if new entries added
        if no_entries_added > 0:
            try:
                with open(self.call_log_filename,'w') as out_file: 
                    json.dump(old_log_entries, out_file, indent=1, sort_keys=True)
            except IOError as e:
                self.logger.error("Cannot write new call_log :" + str(e))

        # Report number of entries added to the local file
        yield GaugeMetricFamily(
            'tg3442de_call_log_local_added',
            'Number of entries added to local Call Log storage',
            value = no_entries_added
        )
