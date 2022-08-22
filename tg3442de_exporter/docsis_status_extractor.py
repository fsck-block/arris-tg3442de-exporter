import re
import json
from logging import Logger
from typing import Iterable, Set, Dict

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor

from prometheus_client import Metric
from prometheus_client.metrics_core import (
    InfoMetricFamily,
    CounterMetricFamily,
    GaugeMetricFamily,
    StateSetMetricFamily,
)

DOCSIS_STATUS   = 'docsis_status'
GET_STATUS_DOCSIS = '/php/status_docsis_data.php'


class DocsisStatusExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger):
        super(DocsisStatusExtractor, self).__init__(
            DOCSIS_STATUS, {GET_STATUS_DOCSIS}, logger
        )
        self.logger = logger

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("DeviceStatusExtractor")

        # parse GlobalSettings
        raw_html = raw_htmls[GET_STATUS_DOCSIS]
        
        if len(raw_html) < -10:
            return
        #print(raw_html)

        # extract json from javascript
        json_downstream_data = re.search(r".*json_dsData = (.+);.*", raw_html)[1]
        json_upstream_data = re.search(r".*json_usData = (.+);.*", raw_html)[1]
        # parse json
        downstream_data = json.loads(json_downstream_data)
        upstream_data = json.loads(json_upstream_data)
        # convert lock status to numeric values
        for d in [ upstream_data, downstream_data ]:
            for c in d:
                if c['LockStatus'] == "ACTIVE" or c['LockStatus'] == "Locked" or c['LockStatus'] == "SUCCESS":
                    c['LockStatus'] = 1
                else:
                    c['LockStatus'] = 0
        
        CHANNEL_ID = "channel_id"
        ds_frequency = GaugeMetricFamily(
            "tg3442de_downstream_frequency",
            "Downstream channel frequency",
            unit="hz",
            labels=[CHANNEL_ID],
        )
        ds_power_level = GaugeMetricFamily(
            "tg3442de_downstream_power_level",
            "Downstream channel power level",
            unit="dbmV",
            labels=[CHANNEL_ID],
        )
        ds_snr = GaugeMetricFamily(
            "tg3442de_downstream_snr",
            "Downstream channel signal-to-noise ratio (SNR)",
            unit="db",
            labels=[CHANNEL_ID],
        )
        ds_locked = GaugeMetricFamily(
            "tg3442de_downstream_locked",
            "Downstream locking status",
            unit="bool",
            labels=[CHANNEL_ID],
        )
        for channel in downstream_data:
            #print(channel)
            channel_id = channel["ChannelID"]
            #channel_type = channel['ChannelType']
            lock_status = channel['LockStatus']
            frequency = channel["Frequency"]
            if type(frequency) is str:
                frequency = frequency.split('~')[0]
            power_level,rxmer = channel["PowerLevel"].split('/')
            snr_level = channel["SNRLevel"]

            labels = [channel_id.zfill(2)]
            ds_locked.add_metric(labels,lock_status)
            ds_frequency.add_metric(labels, float(frequency))
            ds_power_level.add_metric(labels, float(power_level))
            ds_snr.add_metric(labels, float(snr_level))
            #ds_rxmer.add_metric(labels,float(rxmer))
        yield from [ds_frequency, ds_power_level, ds_snr,ds_locked]

        us_frequency = GaugeMetricFamily(
            "tg3442de_upstream_frequency",
            "Upstream channel frequency",
            unit="hz",
            labels=[CHANNEL_ID],
        )
        us_power_level = GaugeMetricFamily(
            "tg3442de_upstream_power_level",
            "Upstream channel power level",
            unit="dbmV",
            labels=[CHANNEL_ID],
        )
        us_locked = GaugeMetricFamily(
            "tg3442de_upstream_locked",
            "Upstream locking status",
            unit="bool",
            labels=[CHANNEL_ID],
        )

        for channel in upstream_data:
            #print(channel)
            channel_id = channel["ChannelID"]
            lock_status = channel['LockStatus']
            frequency = channel["Frequency"]
            if type(frequency) is str:
                frequency = frequency.split('~')[0]
            power_level,rxmer = channel["PowerLevel"].split('/')

            labels = [channel_id.zfill(2)]
            us_locked.add_metric(labels,lock_status)
            us_frequency.add_metric(labels, float(frequency))
            us_power_level.add_metric(labels, float(power_level))
            #ds_rxmer.add_metric(labels,float(rxmer))
        yield from [us_frequency, us_power_level,us_locked]

