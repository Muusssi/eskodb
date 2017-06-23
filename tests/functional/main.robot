*** Settings ***
Library  RequestsLibrary
Library  Collections
Library  testutils

Suite Setup  Suite initialization

*** Test cases ***
Page should be work without login
    [Setup]     Create session   local  http://localhost:8888
    [Template]  Page status ok
    /
    /login
    /game/new/
    /player/new
    /course/new/
    /course/1/
    /course/2/
    /course/3/
    /holes/1/update
    /eskocup/2017/

Page should require login
    [Setup]     Create session   local  http://localhost:8888
    [Template]  Should redirect to login
    /players
    /player/1/update

Adding player should work
    Create session   local  http://localhost:8888
    &{data}=  Create Dictionary  name=Seppo
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /player/new  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    Should be equal as strings  ${resp.url}  http://localhost:8888/
    ${player_id}=  Get player by name  Seppo
    Should not be equal as strings  ${player_id}  None

*** Keywords ***
Page status ok
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${false}
    Should be equal as strings  ${resp.status_code}  200

Should redirect to login
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  http://localhost:8888/login?

Suite initialization
    Initialize test database
