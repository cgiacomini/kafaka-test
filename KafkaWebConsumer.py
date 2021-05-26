#!/bin/env python3

import json, time, logging
import getopt, sys, re
import psycopg2

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from KafkaWebConfig import KafkaWebConfig
from datetime import datetime, timezone

################################################################################

class KafkaWebConsumer():

    ############################################################################
    def __init__(self, polling: int):
                     
        '''
        Initialize website metrics and kafka connection
        Parameters:
            polling (int): polling interval

        ''' 
      
        self._config = KafkaWebConfig()
        self._consumer = None
        self._dbconfig = self._config.database_config()
        self._kafkaconfig = self._config.kafka_config()
        self._polling_interval = polling
         
        # Collected metrics
        self._response_time = 0
        self._status_code = 0
        self._pattern = None
        self._pattern_match = False

        try:
           # initialize logging facility
           logging.basicConfig(filename='KafkaWebConsumer.log', 
                           format='[%(asctime)s] [%(levelname)-4s] %(message)s',
                           level=logging.INFO,
                           datefmt='%Y-%m-%d %H:%M:%S')
 
           # Get Config
           topic_name          = self._kafkaconfig['topic_name']
           auto_offset_reset   = self._kafkaconfig['auto_offset_reset']
           enable_auto_commit  = self._kafkaconfig['enable_auto_commit']
           consumer_timeout_ms = int(self._kafkaconfig['consumer_timeout_ms'])
           broker              = self._kafkaconfig['broker']
           
           # Bootstrap consumer
           self._consumer = KafkaConsumer(topic_name,
                        auto_offset_reset   = auto_offset_reset,
                        enable_auto_commit  = enable_auto_commit,
                        consumer_timeout_ms = consumer_timeout_ms,
                        bootstrap_servers   = broker)

           
           # Connect to postgres and create metrics database and table
           logging.info(f'Succesfully connected to boker: {broker}')
           self.dbConnection = self.create_db('metricsdb', 'metrics')

        except NoBrokersAvailable as ex:
           logging.error(f'No broker available.')
           print(f'No broker available.')
           sys.exit(1)

        except Exception as ex:
          print(str(ex))
          logging.error(f'Exception: {str(ex)} - while initializing Kafka Consumer.')
          sys.exit(1)

    ############################################################################
    def store_statistics(self, message: str):

        obj = json.loads(message)    
        logging.info(f'instert into metrics table values {message}')

        try:
           date_time = datetime.now(timezone.utc)
           query = f"""INSERT INTO metrics VALUES(
                                   '{date_time}',
                                    {obj['status_code']},
                                    {obj['response_time']},
                                   '{obj['pattern']['expression']}',
                                   '{obj['pattern']['match']}',
                                   '{obj['url']}')"""
           cursor = self.dbConnection.cursor()
           cursor.execute(query)
           self.dbConnection.commit()
           cursor.close()
           logging.info('record inserted.')

        except Exception as ex:
          print(str(ex))
          logging.error(f'Exception: {str(ex)} - while initializing Kafka Consumer.')

    ############################################################################
    def start(self):
        
        print ('Collecting statistics ...')
        while True:
          for message in self._consumer:

              value = message.value
              logging.info(f'Message: {value}')
              self.store_statistics(value)

              logging.info(f'Sleeping...')
              time.sleep(self._polling_interval)

   
    ############################################################################
    def create_db(self, database_name: str, table_name: str):

        '''
        Verify and create the database and tables if does not exist yet
        Parameters:
            database_name (str): postgres database for published statistics
            table_name    (str): postgres table    for published statistics
        '''

        connection = None
        connection_params = self._config.database_config()
       
        # Connect to default postgres database
        try :
           logging.info(f'Database connection params : {connection_params}')
           connection = psycopg2.connect(**connection_params)
           logging.info('Succesfully connected to postgres server.')
 
        except Exception as ex:
           logging.error(f'Cannot connect to postgresql server. {ex}')
           raise

        # Verify if metrics database already exists
        try :
           if connection is not None:
              connection.autocommit = True
              cur = connection.cursor()
              cur.execute("SELECT datname FROM pg_database;")
              list_database = cur.fetchall()
              if ((database_name,)) in list_database:
                  logging.info(f"'{database_name}' Database already exist, skip creation")

                  # Connect to metrix database database
                  connection_params['database'] = database_name
                  logging.info(f'Database connection params : {connection_params}')
                  connection = psycopg2.connect(**connection_params)
                  logging.info(f'Succesfully connected to "{database_name}.')
              else:
                  # Creare database and tables
                  logging.info(f"'{database_name}' Database not exist, creating ...")
                  cur.execute(f"CREATE DATABASE {database_name}")
                  # Close connection to default postgres database
                  cur.close()
                  connection.commit()
                  connection.close()
               
                  # Open new connection with new datatabase
                  connection_params['database'] = database_name
                  logging.info(f'Database connection params : {connection_params}')
                  connection = psycopg2.connect(**connection_params)
                  logging.info(f'Succesfully connected to "{database_name}.')

                  logging.info(f"Database: {database_name} {table_name} table Creating...")
                  cur = connection.cursor()
                  cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                                 CREATED_AT TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                 STATUS_CODE INT2,
                                 RESPONSE_TIME FLOAT4,
                                 EXPRESSION VARCHAR(255),
                                 EXPRESSION_MATCH BOOL,
                                 URL VARCHAR(255))
                               """)
                  logging.info(f'Database: {database_name} {table_name} table  Created.')
                  connection.commit()
                  cur.close()
           return connection

        except Exception as ex:
           logging.error(f'Cannot create database {ex}')
           raise

################################################################################
def usage(argv):
    print ('Usage:')
    print (f'\t{argv[0]} [-p <polling>]')
    print ('\twhere:')
    print ('\t  polling   : polling interval. Default 60s')
    sys.exit(2)

################################################################################
def main(argv):

   polling = 60

   try:
      opts, args = getopt.getopt(argv[1:],"p:", ["polling"])
   except getopt.GetoptError as ex:
        print(f'Error: {ex}')
        usage(argv)

   for opt, arg in opts:
      if opt in ("-p", "--polling"):
         polling = int(arg)
   try:
      kc = KafkaWebConsumer(polling)
      kc.start()
   except KeyboardInterrupt:
       print ("Exiting")
   sys.exit(0)



################################################################################
if __name__ == "__main__":
   main(sys.argv)
