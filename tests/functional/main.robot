*** Settings ***
Library  RequestsLibrary
Library  Collections
Library  testutils

Suite Setup  Suite initialization

*** Variables ***
${localhost}    http://localhost:8887

*** Test cases ***
Page should be work without login
    [Setup]     Create session   local  ${localhost}
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
    [Setup]     Create session   local  ${localhost}
    [Template]  Should redirect to login
    /players
    /player/1/update

Adding player should work
    Create session   local  ${localhost}
    &{data}=  Create Dictionary  name=Seppo
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /player/new  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    Should be equal as strings  ${resp.url}  ${localhost}/
    ${player}=  Get player by name  Seppo
    Should not be equal as strings  ${player}  None
    Should not be equal as strings  ${player.id}  None

Adding course should work
    Create session   local  ${localhost}
    &{data}=  Create Dictionary  name=RataC  holes=17
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /course/new/  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${course}=  Get course by name  RataC
    Should not be equal as strings  ${course}  None
    Should not be equal as strings  ${course.id}  None
    Should be equal as strings  ${resp.url}  ${localhost}/holes/${course.id}/update

Starting a new game should work
    Create session   local  ${localhost}
    ${games}=  Get games by course id  1
    Should be true  len($games) == 0
    ${player}=  Get player by name  Vistor
    &{data}=  Create Dictionary  course=1  player=${player.id}
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /game/new/  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${games}=  Get games by course id  1
    Should be true  len($games) == 1
    ${player}=  Get player by name  Vistor
    Should be equal as strings  ${player.active}  ${games[0].id}
    Should start with  ${resp.url}  ${localhost}/game/${games[0].id}



*** Keywords ***
Page status ok
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${false}
    Should be equal as strings  ${resp.status_code}  200

Should redirect to login
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  ${localhost}/login?

Suite initialization
    Initialize test database
