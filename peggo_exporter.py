"""
Peggo Prometheus exporter
Developed by Architect Nodes :)
"""

import os
import time
from prometheus_client import start_http_server, Gauge, Enum
import requests
import json
import logging
import sys

log_level='INFO'
set_polling_interval_seconds = "60"

"""
set_exporter_port - Local Port for HTTP server where metrics will be available
set_api_url - API End point for collecting exporter data. Coule be API URL or http(s)://IP:PORT
set_orchestrator_address - Injective Orchestrator address for your validator
"""
set_exporter_port = "9877"
set_api_url=" "
set_orchestrator_address="inj1xxxx"

#log_format = '%(asctime)s - [%(filename)s:%(lineno)d] -  %(funcName)s - %(levelname)s - %(message)s'

# Define Logger settings - Set Log Level
log_format = '[%(filename)s:%(lineno)d] -  %(funcName)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
#Define StreamHandler, set log format
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(log_level)
#add StreamHandler to Logger
logger.addHandler(handler)

class PeggoMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, api_url, orchestrator_address, polling_interval_seconds):
        
        """
        Initialize Instance variables
        """
        self.api_url = api_url
        self.orchestrator_address = orchestrator_address
        self.polling_interval_seconds = polling_interval_seconds
        self.api_status = 0
        self.last_known_observed_nonce = "0"
        self.last_known_claim_eth_event_nonce = "0"
        self.last_known_pending_valsets = "0"
        self.last_known_pending_batches = "0"

        # Prometheus metrics to collect
        self.last_observed_nonce = Gauge("peggo_last_observed_nonce", "Last Observed Peggo Nonce")
        self.last_claim_eth_event_nonce = Gauge("peggo_last_claim_eth_event_nonce", "Latest Orchestrator Nonce")
        self.pending_valsets = Gauge("peggo_pending_valsets", "Pending Valsets")
        self.pending_batches = Gauge("peggo_pending_batches", "Pending Batches")
        self.peggo_api_status = Gauge("peggo_api_status", "Peggo API Status")

    def run_metrics_loop(self):
        """Metrics fetching loop"""
        logger.info('Fecthing Peggo metrics') 
        while True:
            # Fetch metrics
            self.fetch()
            logger.info('Sleeping for ' + str (self.polling_interval_seconds) + 'sec')
            #Sleep for polling_interval_seconds
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """
        # Update Prometheus metrics with application metrics

        #Check API Node health
        self.peggo_api_status.set(self.get_api_health(self.api_url))

        #If API Node is not available, skip metric collection
        if self.api_status == 0:
            logger.info("API is not available. Skipping metric collection. Will retry.")
            return

        #API Node is available, set metrics from API response
        self.last_observed_nonce.set(self.get_last_observed_nonce(self.api_url))
        self.last_claim_eth_event_nonce.set(self.get_last_claim_eth_event_nonce(self.api_url))
        self.pending_valsets.set(self.get_pending_valsets(self.api_url))
        self.pending_batches.set(self.get_pending_batches(self.api_url))

    def get_api_health(self,api_url):
        """
        Return 1 - if API is available and Node is synced
        Return 0 - if API is not availeble or node is syncing
        """
        logger.info("Checking API Health")
        if self.is_node_synced(api_url) == True:
            logger.info("Setting API Status to 1")
            return str (1)
        else:
            logger.info("Setting API Status to 0")
            return str (0)


    def get_last_observed_nonce(self,api_url):
        """
        Fetching Last Observed Peggo Nonce
        """
        module_state_url=api_url + "/peggy/v1/module_state"
        logger.debug('Fetching Last Observed Peggo Nonce: API Request: ')
        logger.debug(module_state_url)

        #Make API call to get last_observed_nonce
        response = self.submit_api_request(module_state_url)

        #Exception encountered in connectivity, return last known nonce
        #Error already logged in submit_api_request
        if response is  None:
            return self.last_known_observed_nonce

        module_state = response.json()
        logger.debug('Fetching Last Observed Peggo Nonce: API Response: module_state: ')
        logger.debug(module_state)

        #check for error response
        self.check_for_error(module_state)

        self.last_known_observed_nonce = str(module_state['state']['last_observed_nonce'])
        logger.info('Last Observed Peggo Nonce: ' + str(module_state['state']['last_observed_nonce']))

        #return last_observed_nonce
        return (module_state['state']['last_observed_nonce'])

    def get_last_claim_eth_event_nonce(self,api_url):
        """
        Get Latest Orchestrator Nonce
        """

        #Build URL
        event_url=api_url + "/peggy/v1/oracle/event/" + self.orchestrator_address
        logger.debug('Fetching latest Orchestrator Nonce: API Request: ')
        logger.debug(event_url)

        #Make API call to get Latest Orchestrator Nonce
        response = self.submit_api_request(event_url)

        #Exception encountered in connectivity, return last known orchestrator nonce
        #Error already logged in submit_api_request
        if response is  None:
            return self.last_known_claim_eth_event_nonce

        event = response.json()
        logger.debug('Get Latest Orchestrator Nonce: API Response: event: ')
        logger.debug(event)

        #check for error response
        self.check_for_error(event)
        self.last_known_claim_eth_event_nonce = str(event['last_claim_event']['ethereum_event_nonce'])
        logger.info('Latest Orchestrator Nonce: ' + str(event['last_claim_event']['ethereum_event_nonce']))

        #return Latest Orchestrator Nonce
        return (event['last_claim_event']['ethereum_event_nonce'])

    def get_pending_valsets(self,api_url):
        """
        Get Pending Valsets
        """

        #Build URL
        pending_valsets_url=api_url + "/peggy/v1/valset/last?address=" + self.orchestrator_address
        logger.debug('Get Pending Valsets: API Request: ')
        logger.debug(pending_valsets_url)
        
        #Make API call to get pending_valsets
        response = self.submit_api_request(pending_valsets_url)
        
        #Exception encountered in connectivity, return last known pending valsets
        #Error already logged in submit_api_request
        if response is  None:
            return self.last_known_pending_valsets

        pending_valsets = response.json()
        logger.debug('Get Pending Valsets: API Response: pending_valsets: ')
        logger.debug(pending_valsets)

        #check for error response
        self.check_for_error(pending_valsets)
        self.last_known_pending_valsets = str(len(pending_valsets['valsets']))
        logger.info('Pending Valsets: ' + str(len(pending_valsets['valsets'])))

        #return current pending valsets
        return (len(pending_valsets['valsets']))

    def get_pending_batches(self,api_url):
        """
        Get Pending Batches
        """

        #Build URL
        pending_batches_url=api_url + "/peggy/v1/batch/last?address=" + self.orchestrator_address
        logger.debug('Get Pending Batches: API Request: ')
        logger.debug(pending_batches_url)
        
        #Make API call to get pending batches
        response = self.submit_api_request(pending_batches_url)

        #Exception encountered in connectivity, return last known pending valsets
        #Error already logged in submit_api_request
        if response is  None:
            return self.last_known_pending_batches

        pending_batches = response.json()
        logger.debug('Get Pending Batches: API Response: pending_batches: ')
        logger.debug(pending_batches)

        #check for error response
        self.check_for_error(pending_batches)

        #Get pending batches count from API response (pending_batches)
        if "batch" in pending_batches:
            if pending_batches['batch'] is None:
                self.last_known_pending_batches = str(0)
                logger.info('Pending Batches: ' + str(0))
                return 0
            else:
                self.last_known_pending_batches = str(1)
                logger.info('Pending Batches: ' + str(1))
                return 1
        elif "batches" in pending_batches:
            self.last_known_pending_batches = str(len(pending_batches['batches']))
            logger.info('Pending Batches: ' + str(len(pending_batches['batches'])))
            return (len(pending_batches['batches']))
        else:

            #Unable to process message, log error and return last known pending batches
            logger.error('Error encountered in Pending Batches: dumping response message')
            logger.error(pending_batches)
            return self.last_known_pending_batches

    def check_for_error(self,response_message):
        #Check response for error messages
        if "code" in response_message:
            logger.error('Error encountered in response message')
            logger.error(response_message)

            #Exit program
            sys.exit()
        else:

            #No error in response, continue processing
            pass

    def submit_api_request(self, request_url):
        #try request_url and catch any exception
        try:
            response = requests.get(request_url,timeout=10)
            response.raise_for_status()
        except (requests.exceptions.HTTPError,requests.exceptions.ConnectionError,requests.exceptions.Timeout,requests.exceptions.RequestException) as errhttp:
            logger.error("http error: %s", errhttp)

            #Log message if previous api_status was 1
            if self.api_status == 1:
                logger.error("Error Encountered in API call. Will retry.")

            logger.error("Error connecting to API. API is Unhealthy.")

            #Set api_status to 0 since API Node is not available
            self.api_status = 0
            return None

        else:
            
            #Log message for API healthange if prior api_status was 0
            if self.api_status == 0:
                logger.info("Successfully connected to API.")

            # Set API status to 1
            self.api_status = 1

            #Return response object for further processing
            return response

    def is_node_synced(self, api_url):

        # This method checks the connectivity and sync status for API Node 
        logger.info("Checking API Node Status: %s", api_url)

        #Build URL and submit API call
        response = self.submit_api_request(api_url+"/cosmos/base/tendermint/v1beta1/syncing")

        #Exception encountered in connectivity, return False
        #Error already logged in submit_api_request
        if response is  None:
            return False

        else:
            api_status_check = response.json()
            logger.debug(api_status_check)

            #check for error in response
            self.check_for_error(api_status_check)

            #Check for sync status
            if api_status_check['syncing'] == False:
                #Node is synced, log message and return True
                logger.info("API Node is Up and Synced.")
                return True
            else:
                #Node is still syncing, log message and return False
                logger.info("API Node is up but Node is still syncing")
                return False


def main():
    """Main entry point"""
    logger.info('Starting Peggo Exporter')
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", set_polling_interval_seconds))
    exporter_port = int(os.getenv("EXPORTER_PORT", set_exporter_port))
    api_url=set_api_url
    orchestrator_address=set_orchestrator_address

    #Check if default orchestrator_address is present, throw error and exit
    if orchestrator_address == 'inj1xxxx':
        logger.error('Please provide valid Injective Orchestrator Address using set_orchestrator_address param in peggo_exporter.py')
        sys.exit()

    logger.info ('Polling Interval:' + str(polling_interval_seconds) + 'sec')
    logger.info ('Setting Exporter Server Port:' + str(exporter_port))
    logger.info ('Setting API URL:' + api_url)
    logger.info ('Setting Orchestrator Address:' +  orchestrator_address)

    #Create object of PeggoMetrics and pass API URL, Orch Address and polling interval
    peggo_metrics = PeggoMetrics(
        api_url=api_url,
        orchestrator_address=orchestrator_address,
        polling_interval_seconds=polling_interval_seconds
    )
    
    logger.info ('Starting HTTP Server on Port: ' + str(exporter_port))

    #Start HTTP Server
    start_http_server(exporter_port)

    #Calling method to collect metrics
    #run_metrics_loop will collect metrics every polling_interval_seconds
    peggo_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
