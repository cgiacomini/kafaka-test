# kafaka-test
Collect web stats and write them to postgress

## Environment setup

### Setup Python Virtual Enviroment

```
$ python3 -m venv PyEnv
$ source PyEnv/bin/activate
$ pip install -r requirements.txt
$ pip install --upgrade pip
```

### Configuration
Modify **KafkaWebConfig.cfg** configuration file to aligne to your configuration.
Here is an example used in my cygwin environment.

```
[kafka]
broker=localhost:9092
consumer_timeout_ms=1000
#auto_offset_reset=earliest
auto_offset_reset=latest
enable_auto_commit=True
topic_name=web_metrix
num_partitions=3
replica_factor=1

[postgresql]
host=localhost
database=postgres
user=<posgres_user>
password=<postgres_passwd>

```

## Run Kafa Producer
The Producer periodically send and HTTP request to the specified URL and publish some results information to
to the configure kfka topic and broker.
The producer may optionaly check if a given regular expression match the ducoment received via the HTTP request,
the regular expression as well as the match result is also published to kafka.
The Producer activity is logged in *KafkaWebProducer.log* file


```
$ python KafkaWebProducer.py
Usage:
        KafkaWebProducer.py [-p <polling>] [-e<expr>] -u <url>
        where:
          polling   : Web site polling interval. Default 60s
          expr      : regular expression to check aginst returned doc
          url       : Web site URL to monitor
        Example:
        KafkaWebProducer.py -p 10 -e ".*<title>Google</title>.*" -u www.google.com
```

## Run Kafa Producer
The Consumer periodically collect the publish result informations from the configured kafka topic and broker
and store them inside the **metrics** table of the postgress **metricsdb** database.
The the database and table are create by the kafka consumer the very first time it runs.
The Consumer activity is logged in *KafkaWebConsumer.log* file


```
Usage:
        ./KafkaWebConsumer.py [-p <polling>]
        where:
          polling   : polling interval. Default 60s

```
### The database table schema is as follow :
```
 table_name |   column_name    |        data_type
------------+------------------+--------------------------
 metrics    | created_at       | timestamp with time zone
 metrics    | status_code      | smallint
 metrics    | response_time    | real
 metrics    | expression       | character varying
 metrics    | expression_match | boolean
 metrics    | url              | character varying
```
