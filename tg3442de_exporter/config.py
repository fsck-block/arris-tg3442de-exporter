from pathlib import Path
from typing import Union, Dict

from deepmerge import Merger
from ruamel.yaml import YAML

from tg3442de_exporter.device_status_extractor import  DEVICE_STATUS
from tg3442de_exporter.docsis_status_extractor import DOCSIS_STATUS
from tg3442de_exporter.overview_extractor import OVERVIEW_STATUS
from tg3442de_exporter.phone_status_extractor import PHONE_STATUS
from tg3442de_exporter.call_log_extractor import CALL_LOG
from tg3442de_exporter.call_log_local_extractor import CALL_LOG_LOCAL
from tg3442de_exporter.event_log_local_extractor import EVENT_LOG_LOCAL

IP_ADDRESS      = "ip_address"
PASSWORD        = "password"
EXPORTER        = "exporter"
PORT            = "port"
TIMEOUT_SECONDS = "timeout_seconds"
EXTRACTORS      = "metrics"
CALL_LOG_FILE   = 'call_log_filename'
EVENT_LOG_FILE  = 'event_log_filename'
SIMULATE        = "simulate"

# pick default timeout one second less than the default prometheus timeout of 10s
DEFAULT_CONFIG = {
    EXPORTER: {
        PORT: 9706,
        TIMEOUT_SECONDS: 9,
        # EXTRACTORS: {DEVICE_STATUS, DOCSIS_STATUS, OVERVIEW_STATUS, PHONE_STATUS, CALL_LOG, CALL_LOG_LOCAL, EVENT_LOG_LOCAL },
        EXTRACTORS: {DEVICE_STATUS, DOCSIS_STATUS, OVERVIEW_STATUS, PHONE_STATUS },
        SIMULATE : 0,
        CALL_LOG_FILE : 'tg3442de_call_log.json',
        EVENT_LOG_FILE : 'tg3442de_event_log.json',
    }
}


def load_config(config_file: Union[str, Path]) -> Dict:
    """
    Loads and validates YAML config for this exporter and fills in default values
    :param config_file:
    :return: config as dictionary
    """
    yaml = YAML()
    with open(config_file) as f:
        config = yaml.load(f)

    # merge with default config: use 'override' for lists to let users replace extractor setting entirely
    merger = Merger([(list, "override"), (dict, "merge")], ["override"], ["override"])
    config = merger.merge(DEFAULT_CONFIG, config)

    for param in [IP_ADDRESS, PASSWORD]:
        if not param in config:
            raise ValueError(
                f"'{param}' is a mandatory config parameter, but it is missing in the YAML configuration file. Please see README.md for an example."
            )

    if EXPORTER in config.keys():
        if config[EXPORTER][TIMEOUT_SECONDS] <= 0:
            raise ValueError(f"'{TIMEOUT_SECONDS} must be positive.")
        if config[EXPORTER][PORT] < 0 or config[EXPORTER][PORT] > 65535:
            raise ValueError(f"Invalid exporter port.")

        if not config[EXPORTER][EXTRACTORS]:
            raise ValueError(
                "The config file needs to specify at least one family of metrics."
            )
        config[EXPORTER][EXTRACTORS] = sorted(set(config[EXPORTER][EXTRACTORS]))

    return config
