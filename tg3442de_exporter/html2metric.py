from logging import Logger
from typing import Dict

from tg3442de_exporter.html_metrics_extractor import HtmlMetricsExtractor
from tg3442de_exporter.device_status_extractor import DeviceStatusExtractor, DEVICE_STATUS
from tg3442de_exporter.docsis_status_extractor import DocsisStatusExtractor, DOCSIS_STATUS
from tg3442de_exporter.overview_extractor import OverviewExtractor, OVERVIEW_STATUS
from tg3442de_exporter.phone_status_extractor import PhoneStatusExtractor, PHONE_STATUS
from tg3442de_exporter.call_log_extractor import CallLogExtractor, CALL_LOG
from tg3442de_exporter.call_log_local_extractor import CallLogLocalExtractor, CALL_LOG_LOCAL
from tg3442de_exporter.event_log_local_extractor import EventLogLocalExtractor, EVENT_LOG_LOCAL

#TODO: Other pages / extractors
#GET_EVENT_LOG = '/php/status_event_log_data.php?{%22eventLogRecord%22:{}}'

def get_metrics_extractor(ident: str, logger: Logger, exporter_config: Dict):
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
        PHONE_STATUS : PhoneStatusExtractor,
        CALL_LOG_LOCAL : CallLogLocalExtractor,
        CALL_LOG : CallLogExtractor,
        EVENT_LOG_LOCAL : EventLogLocalExtractor,
    }
    if not ident in extractors.keys():
        raise ValueError(
            f"Unknown extractor '{ident}', supported are: {', '.join(extractors.keys())}"
        )
    cls = extractors[ident]
    return cls(logger,exporter_config)

