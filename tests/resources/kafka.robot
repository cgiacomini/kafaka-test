*** Settings ***

Library  Process

*** Variables  ***

*** Keywords ***

################################################################################
Start Kafka Producer
    [Arguments]  ${url}  ${polling}  ${expr}=

    ${ret}=  Start Process  python  KafkaWebProducer.py  
    ...  -p  ${polling}  
    ...  -u  ${url} 
    ...  -e  ${expr}
    ...  alias=KafkaProducer
    [Return]  KafkaProducer


################################################################################
Stop Kafka Producer
    [Arguments]  ${alias}

    ${ret}=  Terminate Process  ${alias}
    [Return]  ${ret}


################################################################################
Start Kafka Consumer
    [Arguments]  ${polling}

    ${ret}=  Start Process  python  KafkaWebConsumer.py
    ...  -p ${polling}
    ...  alias=KafkaConsumer
    [Return]  KafkaConsumer


################################################################################
Stop Kafka Consumer
    [Arguments]  ${alias}

    ${ret}=  Terminate Process  ${alias}
    [Return]  ${ret}
