# peggo-prometheus-exporter

# Installation
Download peggo_exporter.py and place it on your server.

```bash
mkdir $HOME/peggo_exporter
wget -O $HOME/peggo_exporter/peggo_exporter.py https://raw.githubusercontent.com/social244305-Architect/peggo-prometheus-exporter/main/peggo_exporter.py
```

# Pre Requisites
Program was tested with python3 on Ubuntu 22.04. 
- Confirm you have python installed
  ```bash
  python3 -V
  # expected output Python 3.x.x
  Python 3.8.10
  ```
- Import required Python packages (instructions for Ubuntu provided below):
  ```bash
  pip install prometheus-client
  python3 -m pip install requests
  ```

# Usage
Open `peggo_exporter.py` in editor and configure required params:

Required Params - 
  - `set_api_url` -- Provide URL for your Injective API Node (API URL or http(s)://IP:PORT)
  - `set_orchestrator_address` -- Injective Orchestrator address for your validator

Optional Params -
  - `set_exporter_port` -- Port to open HTTP server for Prometheus. Default Port - 9877
  - `et_polling_interval_seconds` -- Refresh interval for metrics. Default - 60sec
  - `log_level` -- Log level for exporter. Possible values - INFO, DEBUG, ERROR. Default - INFO

Exporter can be started with following command:
```bash
python3 peggo_exporter.py
```

# Systemd service

Sample Systemd service file (name - peggo_exporter.service)
```bash
sudo nano /etc/systemd/system/peggo_exporter.py
```

```bash
[Unit]
Description=Peggo Exporter
After=network.target

[Service]
User=<USER>
ExecStart=python3 /home/<USER>/peggo_exporter/peggo_exporter.py 
Restart=always
RestartSec=10
LimitNOFILE=1000

[Install]
WantedBy=multi-user.target
```

**Commands to load the file and start exporter as systemd service**:

`sudo systemctl daemon-reload`

`sudo systemctl enable peggo_exporter.service --now`

`sudo systemctl restart peggo_exporter.service`

**Command to check peggo_exporter logs**:

`sudo journalctl -u peggo_exporter.service -f -o cat`

# Metrics information
**peggo_api_status** -- 
Value         Description
1       -     if API is available and Node is synced
0       -     if API is not availeble or node is syncing

**peggo_last_observed_nonce** -- Last Observed Peggo Nonce

**peggo_last_claim_eth_event_nonce** -- Latest Orchestrator Nonce

**peggo_pending_valsets** -- Pending valsets count

**peggo_pending_batches** -- Pending batches

# Prometheus config:       

- job_name: 'Peggo_Exporter'
  
    scrape_interval: 60s

    static_configs:

      - targets: ['127.0.0.1:9877']  # Set IP location to point to peggo_exporter server
   
Metrics can be used to generate alerts or display in Grafana.

Disclaimer - This code is provided as reference. Code should be considered beta and provided as reference. The material and information contained on this blog/website are for general information purposes only. You should not rely on the content or information on the website as a basis for making any business, legal or any other decisions.  

# Grafana dashboard
Download or copy contents of [grafana_peggo_exporter.json](https://github.com/social244305-Architect/peggo-prometheus-exporter/blob/main/grafana_peggo_exporter.json). In Grafana, click Dashboards in the left-side menu, select import and copy contents of grafana_peggo_exporter.json in "Import via panel json" section. Click load. Select Prometheus as datasource and click import.

**Dashboard example**

<img width="1279" alt="Screen Shot 2023-07-10 at 7 30 37 PM" src="https://github.com/social244305-Architect/peggo-prometheus-exporter/assets/109033531/796351fd-f060-4598-8a15-b3cb8a3a0a27">



