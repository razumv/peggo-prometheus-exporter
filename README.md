# peggo-prometheus-exporter

# Installation
Download peggo_exporter.py and place it on your server. 

# Pre Requisites
Program was tested with python3 on Ubuntu 22.04. 
- Confirm you have python installed
- Import required Python packages (instructions for Ubuntu provided below):
  - pip install prometheus-client
  - python3 -m pip install requests

# Usage
Open peggo_exporter.py in editor and configure required params:

Required Params - 
  - set_api_url -- Provide URL for your Injective API Node (API URL or http(s)://IP:PORT)
  - set_orchestrator_address -- Injective Orchestrator address for your validator

Optional Params -
  - set_exporter_port -- Port to open HTTP server for Prometheus. Default Port - 9877
  - set_polling_interval_seconds -- Refresh interval for metrics. Default - 60sec
  - log_level -- Log level for exporter. Possible values - INFO, DEBUG, ERROR. Default - INFO

Exporter can be started with following command:
**python3 peggo_exporter.py**

# Systemd service

Sample Systemd file (name - peggo_exporter.service)

[Unit]

Description=Peggo Exporter

After=network.target

[Service]

User=USER

ExecStart=python3 /Location/of/peggo_exporter/peggo_exporter.py 

Restart=always

RestartSec=10

LimitNOFILE=1000

[Install]

WantedBy=multi-user.target

**Commands to load the file and start exporter as systemd service**:

sudo systemctl daemon-reload

sudo systemctl restart peggo_exporter.service

**Command to check peggo_exporter logs**:

sudo journalctl -u peggo_exporter.service -f

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
   
Metrics can be used to generate alerts or display in Grafana. A sample Grafana dashboard will be added soon. 

Disclaimer - This code is provided as reference. Code should be considered beta and provided as reference. The material and information contained on this blog/website are for general information purposes only. You should not rely on the content or information on the website as a basis for making any business, legal or any other decisions.  
