#!/bin/bash

################################################################################
SetEnv()
{
   export TOPDIR=`pwd`
   export KAFKA_BROKER
   export KAFKA_TOPIC
   export POSTGRES_DB
   export POSTGRES_HOST
   export POSTGRES_USER
   export POSTGRES_PASSWORD

   envsubst < KafkaWebConfig.template > KafkaWebConfig.cfg
}

################################################################################
GetConfigItem()
{
    echo -n $($TOPDIR/resources/scripts/GetConfigItem.py  \
              $TOPDIR/resources/config/config.txt \
              $1 $2)
}

################################################################################
RunTests()
{
   echo +-------------------------- Using following configuration ---------------------------------+
   echo "[`date`]"
   echo "[`date`] KAFKA_BROKER          : $KAFKA_BROKER"
   echo "[`date`] KAFKA_TOPIC           : $KAFKA_TOPIC"
   echo "[`date`] POSTGRES_HOST         : $POSTGRES_HOST"
   echo "[`date`] POSTGRES_USER         : $POSTGRES_USER"
   echo "[`date`] TEST TAG              : $TAG"
   echo "[`date`]"
   echo +------------------------------------------------------------------------------------------+

   rm -f log.html  output.xml report.html xunit.xml

   robot -x xunit.xml --loglevel info --pythonpath ${TOPDIR} -i $TAG \
         --variable RESOURCES_PATH:${TOPDIR}/tests/resources  \
         --variable KAFKA_BROKER:${KAFKA_BROKER} \
         --variable KAFKA_TOPIC:${KAFKA_TOPIC} \
         --variable POSTGRES_DB:${POSTGRES_DB} \
         --variable POSTGRES_HOST:${POSTGRES_HOST} \
         --variable POSTGRES_USER:${POSTGRES_USER} \
         --variable POSTGRES_PASSWORD:${POSTGRES_PASSWORD} \
         tests/testsuites
   return $?
}

################################################################################
Usage()
{
   echo "Usage: $0 -b<broker> -t<topic_name> -d<postgres_host> -u<db_user> -p<db_pasword> -T <tag>"
   echo "Where:"
   echo " -b : broke      - Kafka broker. ex: localhost:9092"
   echo " -t : topic_name - Kafka topic name"
   echo " -d : postgresql database host"
   echo " -u : postgres admin user"
   echo " -p : postgres amin password"
   echo " -T : tests tag"
   exit 1
}


################################################################################
main()
{
   KAFKA_BROKER=
   KAFKA_TOPIC=
   POSTGRES_DB=metricsdb
   POSTGRES_HOST=
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   TAG=
   
   while getopts "b:t:d:u:p:T:" opt; do
      case "$opt" in
      b)  KAFKA_BROKER=$OPTARG;;
      t)  KAFKA_TOPIC=$OPTARG ;;
      d)  POSTGRES_HOST=$OPTARG ;;
      u)  POSTGRES_USER=$OPTARG ;;
      p)  POSTGRES_PASSWORD=$OPTARG;;
      T)  TAG=$OPTARG;;
      *)  Usage ;;
      esac
   done

   [[ -z $KAFKA_BROKER ]]      && echo "Missing Option -b<broker>"       && Usage
   [[ -z $KAFKA_TOPIC ]]       && echo "Missing Option -t<topic_name>"   && Usage
   [[ -z $POSTGRES_HOST ]]     && echo "Missing Option -d<postgres_host" && Usage
   [[ -z $POSTGRES_USER ]]     && echo "Missing Option -u<db_user>"      && Usage
   [[ -z $POSTGRES_PASSWORD ]] && echo "Missing Option -p<db_pasword>"   && Usage
   [[ -z $TAG ]]               && echo "Missing Option -T<tag>"          && Usage

   SetEnv
   RunTests
   RET=$?
   return $RET
}

################################################################################
main $*

