*** Settings ***
Library  RequestsLibrary

*** Variables ***
${localhost}    http://localhost:8888

*** Test cases ***
Page should work without login
    [Setup]     Create session   local  ${localhost}
    [Template]  Page status ok
    /
    /login
    /course/new/
    /course/1/
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
