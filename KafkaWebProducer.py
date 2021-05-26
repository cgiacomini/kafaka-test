#!/bin/env python3

import requests, json, time, logging
import getopt, sys, re

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from kafka import KafkaProducer, KafkaAdminClient
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
from kafka.admin.new_topic import NewTopic 
from bs4 import BeautifulSoup

from typing import List
from typing import Optional

from KafkaWebConfig import KafkaWebConfig

################################################################################
#
# This class poll a given URL at a regular interval (60 secs by default),
# checks if a given optional pattern is matching the returned document and 
# publish the following statistics on kafka:
#
#     . get http request return_code
#     . get http request elapsed time
#     . [Optional] A given input pattern regular expression and the match result
#                  on the returned document by the get http request.
#

class KafkaWebProducer():

    ############################################################################
    def __init__(self, url: str, expr: str, polling: int):
        '''
        Initialize website metrics and kafka connection
    
        Parameters:
            url     (str): Website URL to send get request to
            expr    (str): Expression to match agaist 
            polling (int): polling interval
    
        '''

        self._config = KafkaWebConfig()
        self._producer = None
        self._kafkaconfig = self._config.kafka_config()

        # Web Site collected metrics
        self._status_code = 0
        self._response_time = 0
        self._pattern = expr
        self._pattern_match = False

        self._url = url
        self._polling_interval = polling
        self._pattern = expr
        self._document = None
        self._topic = None

        try:
           # initialize logging facility
           logging.basicConfig(filename='KafkaWebProducer.log', 
                           format='[%(asctime)s] [%(levelname)-4s] %(message)s',
                           level=logging.INFO,
                           datefmt='%Y-%m-%d %H:%M:%S')

           # Create topic if does not yet exists
           self._create_topic()

           # Bootstrap producer
           broker = self._kafkaconfig['broker']
           self._producer = KafkaProducer(bootstrap_servers=[broker])

           # For semplicity we do not verify Certificate Authority while sendig 
           # http requests to the web site we collect statistics from
           # Here we also disable insecury requests warnings
           requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
           logging.info(f'Succesfully connected to boker: {broker}')

        except NoBrokersAvailable as ex:
           logging.error(f'No broker available.')
           print(f'No broker available.')
           sys.exit(1)

        except Exception as ex:
           logging.error(f'Exception: {str(ex)} - while connecting Kafka.')
           print(ex)
           sys.exit(1)


    ############################################################################
    def _create_topic(self):
        '''
        Create a topic if does not yet exists.
        The TopicAlreadyExistsError is catched and logged if topic exists
        '''

        try:

           # Get config
           num_partition      = int(self._kafkaconfig['num_partitions'])
           replication_factor = int(self._kafkaconfig['replica_factor'])
           topic_name         = self._kafkaconfig['topic_name']
           broker             = self._kafkaconfig['broker']

           # Define topic
           print (f'Creating topic {topic_name} ...')
           self._topic = NewTopic(name = topic_name,
                                  num_partitions = num_partition,
                                  replication_factor = replication_factor)
           # Create topic
           kafka_cli = KafkaAdminClient(bootstrap_servers=[broker])
           response = kafka_cli.create_topics([self._topic])
           kafka_cli.close()
           logging.info(f'topic {topic_name} {response}.')

        except NoBrokersAvailable as ex:
           logging.error(f'No broker available.')
           print(f'No broker available.')
           sys.exit(1)
            
        except TopicAlreadyExistsError as ex:
           logging.warning(f'topic {topic_name} already exists.')
           pass


    ###########################################################################
    def send_request(self, web_url: str,  headers: Optional[str]):
        '''
        Send an http request and and return the response
    
        Parameters:
            web_url (str): Website URL to send get request to
            headers (str): Optional http requests headers
        '''
 
        try:
           # for simplicity we do not verify SLL certificate here
           return requests.get(web_url, headers=headers, verify=False)


        except Exception as ex:
           logging.error(f'Exception: {str(ex)} - while sending get request.')
 
    ###########################################################################
    def publish_statistics(self, key: str):

        '''
        Publish the metrics on kafka
    
        Parameters:
            key   (str): we could attach a key to the message so that all 
                         messages goes to the same partition (not used yet)
        '''

        try:
           if self._status_code == 200:

              # prepare message in json format
              if self._pattern:
                 pattern_stat = { "expression": self._pattern, 
                                  "match" : self._pattern_match}
              else:
                 pattern_stat = { "expression": None,
                                  "match": None}
                 
              message = {"url": self._url,
                         "status_code": self._status_code, 
                         "response_time": self._response_time, 
                         "pattern": pattern_stat}
                         
              value =  json.dumps(message)

              # publish  statistics 
              key_bytes   = bytes(key,   encoding='utf-8')
              value_bytes = bytes(value, encoding='utf-8')

              #self._producer.send(self._topic.name, key=key_bytes, value=value_bytes)
              self._producer.send(self._topic.name, value=value_bytes)
              self._producer.flush()
              logging.info(f'Statistics published successfully.')

        except Exception as ex:
           logging.error(f'Exception: {str(ex)} - while publish statistics.')
           raise

    ###########################################################################
    def start(self):
        '''
        Loop over http GET request and publish result
        '''

        print ('Publishing statistics ...')
        headers = { 'Cache-Control': 'no-cache' }
        while True :
           response = self.send_request(self._url, headers)

           # Set metrics with info from the response
           if response.status_code == 200 :
              self._status_code   = response.status_code
              self._document      = response.text
              self._response_time = response.elapsed.total_seconds()

              # check if pattern is present in returned document
              if self._pattern:
                 p = re.compile(self._pattern, re.DOTALL)
                 if p.match(self._document):
                    self._pattern_match = True
                 else:
                    self._pattern_match = False

           self.publish_statistics('web_stats')
           time.sleep(self._polling_interval)


################################################################################
def usage(argv):
    print ('Usage:')
    print (f'\t{argv[0]} [-p <polling>] [-e<expr>] -u <url>')
    print ('\twhere:')
    print ('\t  polling   : Web site polling interval. Default 60s')
    print ('\t  expr      : regular expression to check aginst returned doc')
    print ('\t  url       : Web site URL to monitor')
    print ('\tExample:')
    print (f'\t{argv[0]} -p 10 -e ".*<title>Google</title>.*" -u www.google.com')
    sys.exit(2)


###############################################################################
def main(argv):

   polling = 60
   polling = None
   url = None
   expr = None

   try:
      opts, args = getopt.getopt(argv[1:],"u:p:e:", ["url=","polling","expr="])

   except getopt.GetoptError as ex:
        print(f'Error: {ex}')
        usage(argv)

   for opt, arg in opts:
      if opt in ("-u", "--url"):
         url = arg
      elif opt in ("-e", "--expr"):
         expr = arg
      elif opt in ("-p", "--polling"):
         polling = int(arg)
 
   if url and "http://" not in url:
      url = "http://" + url

   if None in {url}:
      usage(argv)

   try: 
     # Start statistics collection
     k = KafkaWebProducer(url, expr, polling)
     k.start()
   except KeyboardInterrupt:
       print ("Exiting")
   sys.exit(0)

################################################################################

if __name__ == "__main__":
   main(sys.argv)
