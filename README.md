# ARRIS TG3442DE Exporter
A [Prometheus](https://prometheus.io/) exporter for monitoring ARRIS TG3442DE cable modems (Firmware AR01.04.046.17_060822_7244.SIP.10.X1). These are sold under the name "Vodafone Station" by Vodafone in Germany

Inspired and based on [Connectbox Prometheus](https://github.com/mbugert/connectbox-prometheus) by [@mburgert](https://github.com/mbugert) (thanks!).
For alternative access to your device see also [vodafone-station-cli](https://github.com/totev/vodafone-station-cli)

## Status
This is work in progress. The software may have bugs and failures. There is no 
specification of the scraped data from TG3442DE, so reverse engineering took place.

Metrics "call_log_local" and "event_log_local" are experimental and at least "event_log_local"
takes a bit too long to be scraped every minute.

## Installation
Simply copy code to target directory 

## Configuration
This exporter queries exactly one TG3442DE cable router as a remote target.
The metrics scraper "call_log_local" and "event_log_local" write the call-log and
the event-log to local disk and report the number of entries added.
To get started, modify `config.yml` from this repository or start out with the following content:
```yaml
# TG3442DE IP address
ip_address: 192.168.0.1

# TG3442DE web interface password
password: WhatEverYourPasswordIs

# All following parameters are optional.
exporter:
  # port on which this exporter exposes metrics (default: 9706)
  #port: 9706

  # filename to store call log
  # call_log_filename : 'tg3442de_call_log.json'

  # filename to store event log
  # event_log_filename : 'tg3442de_event_log.json'

  # timeout duration for connections to the TG3442DE (default: 9)
  #timeout_seconds: 9

  # Customize the family of metrics to scrape. By default, the 
  # log-metrics (call_log_local and event_log_local) are not scraped.
  #metrics: [device_status, docsis_status, overview_status, phone_status, call_log_local, event_log_local ]

```

## Usage
```sh-session
$ python3 tg3442de_exporter path/to/your/config.yml 
```

## Prometheus Configuration
Add the following to your `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'vodafone_station'
    static_configs:
      - targets:
        - localhost:9706
```
One scrape takes roughly 5 seconds for default and 12 seconds including "call_log_local" 
and "event_log_local". Be aware to set the prometheus timeout acordingly.

## Exported Metrics
| Metric name                            | Scraper         | Description                                      |
|:---------------------------------------|:----------------|:-------------------------------------------------|
| `tg3442de_device_info`                 | device_status   | Assorted device information                      |
| `tg3442de_uptime_seconds`              | device_status   | Device uptime in seconds                         |
| `tg3442de_downstream_frequency_MHz`    | docsis_status   | Downstream channel frequency                     |
| `tg3442de_downstream_power_level_dbmV` | docsis_status   | Downstream channel power level                   |
| `tg3442de_downstream_snr_db`           | docsis_status   | Downstream channel signal-to-noise ratio (SNR)   |
| `tg3442de_downstream_locked`           | docsis_status   | Downstream channel locking status                |
| `tg3442de_upstream_frequency_MHz`      | docsis_status   | Upstream channel frequency                       |
| `tg3442de_upstream_power_level_dbmV`   | docsis_status   | Upstream channel power level                     |
| `tg3442de_upstream_locked`             | docsis_status   | Upstream channel locking status                  |
| `tg3442de_device_status`               | overview_status | Assorted device status information               |
| `tg3442de_lan_host_nums`               | overview_status | Number of LAN hosts                              |
| `tg3442de_primary_wlan_host_nums`      | overview_status | Number of primary WLAN hosts                     |
| `tg3442de_guest_wlan_host_nums`        | overview_status | Number of guest WLAN hosts                       |
| `tg3442de_ethernet_client_speed_mbit`  | overview_status | Maximum speed of connected ethernet clients      |
| `tg3442de_primary_wlan_linkrate`       | overview_status | Maximum speed of connected Wi-Fi clients         |
| `tg3442de_guest_wlan_linkrate`         | overview_status | Maximum speed of connected Wi-Fi clients         |
| `tg3442de_phone_status`                | phone_status    | Phone status information                         |
| `tg3442de_call_log_local_added`        | call_log_local  | Number of call log entries added to local file   |
| `tg3442de_event_log_local_added`       | event_log_local | Number of event log entries added to local file  |
| `tg3442de_scrape_duration_seconds`     |                 | ARRIS TG3442DE exporter scrape duration          |
| `tg3442de_up`                          |                 | ARRIS TG3442DE exporter scrape success           |

