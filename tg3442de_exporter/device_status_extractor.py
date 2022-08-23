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


DEVICE_STATUS   = 'device_status'
GET_STATUS_STATUS = '/php/status_status_data.php'


class DeviceStatusExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger):
        super(DeviceStatusExtractor, self).__init__(
            DEVICE_STATUS, {GET_STATUS_STATUS}, logger
        )
        self.logger = logger

    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("DeviceStatusExtractor")

        # parse GlobalSettings
        raw_html = raw_htmls[GET_STATUS_STATUS]
        if len(raw_html) < 10:
            return

        #var js_SerialNumber = 'XXXXXXXXXXX';
        serial_number = self.re_search(r".*var js_SerialNumber = '(.*)';.*",raw_html,1)[0]
        #var js_FWVersion = 'AR01.04.046.17_060822_7244.SIP.10.X1';
        firmware_version = self.re_search(r".*var js_FWVersion = '(.*)';.*",raw_html,1)[0]
        #var js_HWTypeVersion = '7';
        hardware_version  = self.re_search(r".*var js_HWTypeVersion = '(.*)';.*",raw_html,1)[0]

        yield InfoMetricFamily(
            'tg3442de_device',
            'Assorted device information',
            value={
                'serial_number': serial_number,
                'hardware_version': hardware_version,
                'firmware_version': firmware_version,
            },
        )

        #var js_UptimeSinceReboot = '32,00,59';
        uptime = self.re_search(r".*var js_UptimeSinceReboot = '(\d+),(\d+),(\d+)';.*",raw_html,3,default=0)
        uptime_seconds = int(uptime[0])*86400 + int(uptime[1])*3600 + int(uptime[2])*60

        yield GaugeMetricFamily(
            "tg3442de_uptime",
            "Device uptime in seconds",
            unit="seconds",
            value=uptime_seconds,
        )
