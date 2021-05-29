*** settings ***

Resource    ${RESOURCES_PATH}/common.robot

Test Setup     Connet To Postgresql
Test Teardown  Disconnect From Postgresql

*** Keywords ***

*** Variables ***

*** test cases ***

###############################################################################
# Poll www.google.com No expression 2sec polling
# Check logs for expected pattern
# Check Database for expected rows
#
TEST_001
    [Tags]  all
    [Documentation]  Poll www.google.com No expression 2sec polling

    Remove File  KafkaWebProducer.log
    Remove File  KafkaWebConsumer.log

    # Let run Kafka Producer for 20s whith a polling intervall of 2s
    ${alias_p}=  Start Kafka Producer  www.google.com  2
    ${alias_c}=  Start Kafka Consumer  2

    BuiltIn.Sleep  20

    # Stop Kafka Producer and Cosumer  and check log file for expected patterns
    Stop Kafka Producer  ${alias_p}
    Stop Kafka Consumer  ${alias_c}

    Should Match In Log File  KafkaWebProducer.log  .*connecting to localhost:9092.*
    Should Match In Log File  KafkaWebProducer.log  .*Connection complete.*
    Should Match In Log File  KafkaWebProducer.log  .*Statistics published successfully.*

    Should Match In Log File  KafkaWebConsumer.log  .*Succesfully connected to metricsdb.*
    Should Match In Log File  KafkaWebConsumer.log  .*INSERT INTO metrics VALUES.*
    Should Match In Log File  KafkaWebConsumer.log  .*www.google.com.*
    Should Match In Log File  KafkaWebConsumer.log  .*record inserted.*

    # Check if messages have been stored in postgresql
    ${rows}=  Count Rows In Posgress Table   
    Should Be True  ${rows} > 0


###############################################################################
# Poll www.google.com with expression MATCH and 2sec polling
# Check logs for expected pattern
# Check Database for expected rows
#
TEST_002
    [Tags]  all
    [Documentation]  Poll www.google.com with expression match and 2sec polling

    Remove File  KafkaWebProducer.log
    Remove File  KafkaWebConsumer.log

    # Let run Kafka Producer for 20s whith a polling intervall of 2s
    ${alias_p}=  Start Kafka Producer  www.google.com  2  .*<title>Google</title>.*
    ${alias_c}=  Start Kafka Consumer  2

    BuiltIn.Sleep  20

    # Stop Kafka Producer  and check log file for expected patterns
    Stop Kafka Producer  ${alias_p}
    Stop Kafka Consumer  ${alias_c}

    Should Match In Log File  KafkaWebProducer.log  .*connecting to localhost:9092.*
    Should Match In Log File  KafkaWebProducer.log  .*Connection complete.*
    Should Match In Log File  KafkaWebProducer.log  .*send HTTP request http://www.google.com.*
    Should Match In Log File  KafkaWebProducer.log  .*Statistics published successfully.*

    Should Match In Log File  KafkaWebConsumer.log  .*Succesfully connected to metricsdb.*
    Should Match In Log File  KafkaWebConsumer.log  .*INSERT INTO metrics VALUES.*
    Should Match In Log File  KafkaWebConsumer.log  .*www.google.com.*
    Should Match In Log File  KafkaWebConsumer.log  .*record inserted.*

    # Check if messages have been stored in postgresql
    ${rows}=  Count Rows In Posgress Table  where expression like '%Google%'
    Should Be True  ${rows} > 0


###############################################################################
# Poll www.google.com with expression NO MATCH and 2sec polling
# Check logs for expected pattern
# Check Database for expected rows
#
TEST_003
    [Tags]  all
    [Documentation]  Poll www.google.com with expression match and 2sec polling

    Remove File  KafkaWebProducer.log
    Remove File  KafkaWebConsumer.log

    # Let run Kafka Producer for 20s whith a polling intervall of 2s
    ${alias_p}=  Start Kafka Producer  www.google.com  2  .*<title>Amazone</title>.*
    ${alias_c}=  Start Kafka Consumer  2

    BuiltIn.Sleep  20

    # Stop Kafka Producer  and check log file for expected patterns
    Stop Kafka Producer  ${alias_p}
    Stop Kafka Consumer  ${alias_c}

    Should Match In Log File  KafkaWebProducer.log  .*connecting to localhost:9092.*
    Should Match In Log File  KafkaWebProducer.log  .*Connection complete.*
    Should Match In Log File  KafkaWebProducer.log  .*send HTTP request http://www.google.com.*
    Should Match In Log File  KafkaWebProducer.log  .*Statistics published successfully.*

    Should Match In Log File  KafkaWebConsumer.log  .*Succesfully connected to metricsdb.*
    Should Match In Log File  KafkaWebConsumer.log  .*INSERT INTO metrics VALUES.*
    Should Match In Log File  KafkaWebConsumer.log  .*www.google.com.*
    Should Match In Log File  KafkaWebConsumer.log  .*record inserted.*

    # Check if messages have been stored in postgresql
    ${rows}=  Count Rows In Posgress Table  where expression like '%Amazone%' and expression_match is false;
    Should Be True  ${rows} > 0

