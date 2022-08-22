import re
import json
from datetime import timedelta
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Iterable, Set, Dict

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor
from tg3442de_exporter.device_status_extractor import DeviceStatusExtractor, DEVICE_STATUS
from tg3442de_exporter.docsis_status_extractor import DocsisStatusExtractor, DOCSIS_STATUS
from tg3442de_exporter.overview_extractor import OverviewExtractor, OVERVIEW_STATUS


#GET_STATUS_LAN = '/php/status_lan_data.php?lanData%5BdhcpDevInfo%5D=&lanData%5BwifiDev%5D=&lanData%5Bip6Lan%5D='
#GET_STATUS_PHONE = '/php/status_voice_data.php'
#GET_EVENT_LOG = '/php/status_event_log_data.php?{%22eventLogRecord%22:{}}'
#GET_CALL_LOG = '/php/phone_call_log_data.php?{%22PhoneLogRecord%22:{}}'




def get_metrics_extractor(ident: str, logger: Logger):
    """
    Factory method for metrics extractors.
    :param ident: metric extractor identifier
    :param logger: logging logger
    :return: extractor instance
    """
    logger.debug("get_metrics_extractor :"+ident)
    extractors = {
        DEVICE_STATUS: DeviceStatusExtractor,
        DOCSIS_STATUS: DocsisStatusExtractor,
        OVERVIEW_STATUS: OverviewExtractor,
    }
    if not ident in extractors.keys():
        raise ValueError(
            f"Unknown extractor '{ident}', supported are: {', '.join(extractors.keys())}"
        )
    cls = extractors[ident]
    return cls(logger)

