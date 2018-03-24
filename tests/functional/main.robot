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

Playing a game should work
    Create session   local  ${localhost}
    ${course}=  Get course by name  Robotin testirata
    ${games}=  Get active games by course id  ${course.id}
    Should be true  len($games) == 0
    ${player}=  Get player by name  Visitor
    # Start new game
    &{data}=  Create Dictionary  course=${course.id}  player=${player.id}
    &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
    ${resp}=  Post Request  local  /game/new/  allow_redirects=${true}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${games}=  Get active games by course id  ${course.id}
    Should be true  len($games) == 1
    ${game}=  Set Variable  ${games[0]}
    ${player}=  Get player by name  Visitor
    Should be equal as strings  ${player.active}  ${game.id}
    Should be equal as strings  ${resp.url}  ${localhost}/game/${game.id}/
    Page status ok  /game/${game.id}/

    ${results}=  Get results by game id  ${game.id}

    ${expected}=  Create list  None  None  None  None  None  None
    Results are as expected  ${game}  ${expected}
    # Post results
    &{data}=  Create Dictionary  result=${results[0].id}  player=${player.id}  throws=4  penalty=1  approaches=  puts=
    ${resp}=  Post Request  local  /game/${game.id}/  allow_redirects=${false}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${expected}=  Create list  4  None  None  None  None  None
    Results are as expected  ${game}  ${expected}
    Page status ok  /game/${game.id}/

    &{data}=  Create Dictionary  result=${results[2].id}  player=${player.id}  throws=2  penalty=1  approaches=  puts=
    ${resp}=  Post Request  local  /game/${game.id}/  allow_redirects=${false}  data=${data}  headers=${headers}
    Should be equal as strings  ${resp.status_code}  200
    ${expected}=  Create list  4  None  2  None  None  None
    Results are as expected  ${game}  ${expected}
    Page status ok  /game/${game.id}/

    End game  ${game}
    ${games}=  Get active games by course id  ${course.id}
    Should be true  len($games) == 0
    Page status ok  /course/${course.id}/




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

Results are as expected
    [Arguments]  ${game}  ${expected}
    ${results}=  Get results by game id  ${game.id}
    Should be true  len($results) == len($expected)
    ${results_ok}=  Check results as expected  ${results}  ${expected}
    Should be true  ${results_ok}

End game
    [Arguments]  ${game}
    ${resp}=  Get Request  local  /game/end/${game.id}/  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  ${localhost}/


Suite initialization
    Initialize test database
