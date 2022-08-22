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
OVERVIEW_STATUS = 'overview_status'

GET_OVERVIEW      = '/php/overview_data.php'

class OverviewExtractor(HtmlMetricsExtractor):
    def __init__(self, logger: Logger):
        super(OverviewExtractor, self).__init__(
            OVERVIEW_STATUS, {GET_OVERVIEW}, logger
        )
        self.logger = logger

    def add_devices(self,wlan_devices, metric : GaugeMetricFamily,link_speed):
        for device in wlan_devices:
            index = device["Index"]
            link_rate = str(device[link_speed]).split(' ')[0] # handle speed and linkRate
            if  type(link_rate) is str:
                link_rate = 0.0
            hostname = device['HostName']
            mac = device['MAC']
            ipV4 = device['IPv4']
            ipV6 = device['IPv6']
            labels = [str(index),hostname,mac,ipV4,ipV6]
            metric.add_metric(labels,link_rate)


    def extract(self, raw_htmls: Dict[str, bytes]) -> Iterable[Metric]:
        self.logger.debug("OverviewExtractor")

        # parse GlobalSettings
        raw_html = raw_htmls[GET_OVERVIEW]
        
        if len(raw_html) < -10:
            return
        #print(raw_html)

        # extract json from javascript
        json_lan_devices= re.search(r".*json_lanAttachedDevice = (.+);.*", raw_html)[1]
        json_prim_wlan_devices = re.search(r".*json_primaryWlanAttachedDevice = (.+);.*", raw_html)[1]
        json_guest_wlan_devices = re.search(r".*json_guestWlanAttachedDevice = (.+);.*", raw_html)[1]

        lan_host_nums = re.search(r".*js_lanHostNums = '(.+)';.*", raw_html)[1]
        prim_wlan_host_nums = re.search(r".*js_primaryWlanHostNums = '(.+)';.*", raw_html)[1]
        guest_wlan_host_nums = re.search(r".*js_guestWlanHostNums = '(.+)';.*", raw_html)[1]

        yield GaugeMetricFamily(
            "tg3442de_lan_host_nums",
            "Number of LAN hosts",
            unit="",
            value=int(lan_host_nums),
        )
        yield GaugeMetricFamily(
            "tg3442de_primary_wlan_host_nums",
            "Number of primary WLAN hosts",
            unit="",
            value=int(prim_wlan_host_nums),
        )
        yield GaugeMetricFamily(
            "tg3442de_guest_wlan_host_nums",
            "Number of guest WLAN hosts",
            unit="",
            value=int(guest_wlan_host_nums),
        )

        # parse json
        lan_devices = json.loads(json_lan_devices)
        prim_wlan_devices = json.loads(json_prim_wlan_devices)
        guest_wlan_devices = json.loads(json_guest_wlan_devices)

        # set up ethernet user speed metric
        lan_speed = GaugeMetricFamily(
            "tg3442de_lan_speed",
            "Ethernet client network speed",
            unit="MHz",
            labels=['index','hostname','MAC','IPv4','IPv6'],
        )
        self.add_devices(lan_devices, lan_speed,'Speed')
        yield from [lan_speed]

        # set up primary wifi user linkrate  metric
        prim_wlan_linkrate = GaugeMetricFamily(
            "tg3442de_primary_wlan_linkrate",
            "Primary WLAN client link rate",
            unit="MHz",
            labels=['index','hostname','MAC','IPv4','IPv6'],
        )
        self.add_devices(prim_wlan_devices, prim_wlan_linkrate,'LinkRate')
        yield from [prim_wlan_linkrate]

        # set up guest wifi user linkrate  metric
        guest_wlan_linkrate = GaugeMetricFamily(
            "tg3442de_guest_wlan_linkrate",
            "Guest WLAN client link rate",
            unit="MHz",
            labels=['index','hostname','MAC','IPv4','IPv6'],
        )
        self.add_devices(guest_wlan_devices, guest_wlan_linkrate,'LinkRate')
        yield from [guest_wlan_linkrate]

        cm_operational    = self.re_search(r".*js_isCmOperational = '(.*)';.*",raw_html,1)[0]
        prim_wifi_enable  = self.re_search(r".*js_wifiEnable = '(.*)';.*",raw_html,1)[0]
        guest_wifi_enable = self.re_search(r".*js_guestWifiEnable = '(.*)';.*",raw_html,1)[0]
        wps_enable        = self.re_search(r".*js_wpsEnable = '(.*)';.*",raw_html,1)[0]
        schedule_enable   = self.re_search(r".*js_scheduleEnable = '(.*)';.*",raw_html,1)[0]

        yield InfoMetricFamily(
            'tg3442de_device_status',
            'Assorted device status information',
            value={
                'cm_operational': cm_operational,
                'primary_wifi_enable': prim_wifi_enable,
                'guest_wifi_enable': guest_wifi_enable,
                'wps_enable' : wps_enable,
                'schedule_enable' : schedule_enable,
            },
        )
