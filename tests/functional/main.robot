*** Settings ***
Library  RequestsLibrary
Library  Collections
Library  testutils

Suite Setup  Suite initialization

*** Variables ***
${localhost}    http://localhost:8887

*** Test cases ***
Page should work without login
    [Setup]     Create session   local  ${localhost}
    [Template]  Page status ok
    /
    /login
    /course/new/
    /course/1/
    /course/2/
    /course/3/
    /course/1/graph
    /holes/1/update
    /player/new
    /games/
    /game/new/
    /eskocup/2017/

Page should work and redirect to main page
    [Setup]     Create session   local  ${localhost}
    [Template]  Should redirect to main page
    /logout
    /restart/

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
    &{data}=  Create Dictionary  name=Fun course  holes=17
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /course/new/  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${course}=  Get course by name  Fun course
    Should not be equal as strings  ${course}  None
    Should not be equal as strings  ${course.id}  None
    Should be equal as strings  ${resp.url}  ${localhost}/holes/${course.id}/update

Starting a new game should work
    Create session   local  ${localhost}
    ${games}=  Get games by course id  1
    Should be true  len($games) == 0
    ${player}=  Get player by name  Visitor
    &{data}=  Create Dictionary  course=1  player=${player.id}
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /game/new/  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${games}=  Get games by course id  1
    Should be true  len($games) == 1
    ${player}=  Get player by name  Visitor
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

Should redirect to main page
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  ${localhost}/

Suite initialization
    Initialize test database
