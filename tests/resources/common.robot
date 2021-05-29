*** Settings ***

Library  String
Library  OperatingSystem
Library  Collections
Library  DatabaseLibrary


Resource  ${RESOURCES_PATH}/kafka.robot

*** Variables  ***

*** Keywords ***

################################################################################
Connet To Postgresql
    Connect To Database  psycopg2  ${POSTGRES_DB}  ${POSTGRES_USER}
    ...   ${POSTGRES_PASSWORD}  ${POSTGRES_HOST}  5432
    Execute Sql String  Delete from metrics
    
################################################################################
Disconnect From Postgresql
    Execute Sql String  Delete from metrics
    Disconnect From Database

################################################################################
Should Match In Log File
    [Arguments]  ${logfile}  ${regex}

    ${log_content}=  Get File  ${logfile}
    ${ret}=  Get Lines Matching Regexp  ${log_content}  ${regex}
    Should Match Regexp  ${ret}   ${regex}

################################################################################
Count Rows In Posgress Table
    [Arguments]  ${where_clause}=None

    ${rows}=  Row Count  select * from metrics ${where_clause}
    [Return]   ${rows}

################################################################################
#Should Match In Database
    #[Arguments]  ${query}  ${regex}
   # 
    #${ret}=  Excute Sql String  Select * from metrics
    #Should Match Regexp  ${ret}   ${regex}
    #[Return]  ${ret}
