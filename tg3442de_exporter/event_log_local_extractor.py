from logging import Logger
from typing import Iterable, Set, Dict
import json

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor
from prometheus_client import Metric
from prometheus_client.metrics_core import (
    GaugeMetricFamily,
)


EVENT_LOG_LOCAL = 'event_log_local'
GET_EVENT_LOG_LOCAL = '/php/status_event_log_data.php?{%22eventLogRecord%22:{}}'


class EventLogLocalExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger, exporter_config: Dict):
        super(EventLogLocalExtractor, self).__init__(
            EVENT_LOG_LOCAL, {GET_EVENT_LOG_LOCAL}, logger
        )
        self.logger = logger
        self.event_log_filename = exporter_config['event_log_filename']

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("EventLogLocal")

        # parse Event Log
        raw_html = raw_htmls[GET_EVENT_LOG_LOCAL]
        if len(raw_html) < 10:
            return
        # parse json
        json_event_log_dat = json.loads(raw_html)

        event_log_record = json_event_log_dat['eventLog']
        no_entries = len(event_log_record)
        if no_entries == 0:
            return
        no_entries_added = 0
        log_entries = {}
        for log_entry in event_log_record:    
            key = "{}-{}".format(log_entry['Timestamp'],log_entry['Index'])
            log_entries[key] = log_entry

        # TODO: For large event logs work on files directly and not in memory
        # read stored event log
        old_log_entries = {}
        try:
            with open(self.event_log_filename,'r') as in_file: 
              old_log_entries = json.load(in_file)
        except IOError as e:
            self.logger.info("Cannot read old event_log :" +str(e))
        no_old_entries = len(old_log_entries)

        # merge entries
        old_log_entries.update(log_entries)
        
        # save event log
        try:
            with open(self.event_log_filename,'w') as out_file: 
                json.dump(old_log_entries, out_file, indent=1, sort_keys=True)
        except IOError as e:
            self.logger.error("Cannot write new event_log :" + str(e))
        no_entries_added = len(old_log_entries) - no_old_entries
          

        # Report number of entries added to the local file
        yield GaugeMetricFamily(
            'tg3442de_event_log_local_added',
            'Number of entries added to local Event Log storage',
            value = no_entries_added
        )
