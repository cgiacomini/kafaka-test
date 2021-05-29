pipeline {

    agent {
        docker {
            image 'python:3'
            args '-u root -v /var/run/docker.sock:/var/run/docker.sock -h dockcont1'
            reuseNode true
        }
    }

    parameters {
        string(name: 'TAG',               defaultValue: 'all',            description: 'Robot framework test tag to be execute')
        string(name: 'KAFAK_BROKER_HOST', defaultValue: 'localhost:9092', description: 'Kafka broker host:port')
        string(name: 'TOPIC_NME',         defaultValue: 'mymetrics',      description: 'Kafka topic name were messages are published')
        string(name: 'DATABASE_HOST',     defaultValue: 'localhost',      description: 'Posgresql database hostname')
        string(name: 'DB_USER',           defaultValue: 'postgres' ,      description: 'Postgres username')
        string(name: 'DB_PASSWORD',       defaultValue: 'postgres' ,      description: 'Postgres user password')
    }

    stages {
        stage('setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install --upgrade pip'
            }
        }
        stage('Run E2E Tests') {
            steps {
                sh "./run_tests.sh -b ${params.KAFAK_BROKER_HOST} -t ${params.TOPIC_NME} -d ${params.DATABASE_HOST} -u ${params.DB_USER} -p '${params.DB_PASSWORD}' -T ${params.TAG}"
            }
        }
    }
}
