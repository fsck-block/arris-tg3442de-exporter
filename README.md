# ARRIS TG3442DE Exporter
A [Prometheus](https://prometheus.io/) exporter for monitoring ARRIS TG3442DE cable modems. These are sold under the name "Vodafone Station" by Vodafone in Germany

Inspired and based on [Connectbox Prometheus](https://github.com/mbugert/connectbox-prometheus) by [@mburgert](https://github.com/mbugert) (thanks!).
For alternative access to your device see also [vodafone-station-cli](https://github.com/totev/vodafone-station-cli)

## Installation
Simply copy code to target directory 


## Configuration
This exporter queries exactly one TG3442DE cable router as a remote target.
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

  # timeout duration for connections to the TG3442DE (default: 9)
  #timeout_seconds: 9

  # Customize the family of metrics to scrape. By default, all metrics are scraped.
  #metrics: [device_status, docsis_status, overview_status ]

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
One scrape takes roughly 4 seconds.

## Exported Metrics
| Metric name                            | Description                                    |
|:---------------------------------------|:-----------------------------------------------|
| `tg3442de_device_info`                 | Assorted device information                    |
| `tg3442de_uptime_seconds`              | Device uptime in seconds                       |
| `tg3442de_device_status`               | Assorted device status inforation              |
| `tg3442de_downstream_frequency_hz`     | Downstream channel frequency                   |
| `tg3442de_downstream_power_level_dbmV` | Downstream channel power level                 |
| `tg3442de_downstream_snr_db`           | Downstream channel signal-to-noise ratio (SNR) |
| `tg3442de_downstream_locked`           | Downstream channel locking status              |
| `tg3442de_upstream_frequency_hz`       | Upstream channel frequency                     |
| `tg3442de_upstream_power_level_dbmV`   | Upstream channel power level                   |
| `tg3442de_upstream_locked`             | Upstream channel locking status                |
| `tg3442de_lan_host_nums`               | Number of LAN hosts                            |
| `tg3442de_primary_wlan_host_nums`      | Number of primary WLAN hosts                   |
| `tg3442de_guest_wlan_host_nums`        | Number of guest WLAN hosts                     |
| `tg3442de_ethernet_client_speed_mbit`  | Maximum speed of connected ethernet clients    |
| `tg3442de_primary_wlan_linkrate`       | Maximum speed of connected Wi-Fi clients       |
| `tg3442de_guest_wlan_linkrate`         | Maximum speed of connected Wi-Fi clients       |
| `tg3442de_scrape_duration_seconds`     | ARRIS TG3442DE exporter scrape duration        |
| `tg3442de_up`                          | ARRIS TG3442DE exporter scrape success         |

