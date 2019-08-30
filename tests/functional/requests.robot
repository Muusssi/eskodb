*** Settings ***
Library  RequestsLibrary

*** Variables ***
${TARGET_URL}=      http://localhost:8887

*** Test cases ***
Page should work without login
    [Setup]     Create session   local  ${TARGET_URL}
    [Template]  Page status ok
    /
    /login
    /course/new/
    /course/1/
    /course/1/graph
    /holes/1/update
    /player/new
    /game/new/
    /eskocup/2017/
    /eskocup/2018/
    /eskocup/2019/

Page should work and redirect to main page
    [Setup]     Create session   local  ${TARGET_URL}
    [Template]  Should redirect to main page
    /logout
    /restart/

Page should require login
    [Setup]     Create session   local  ${TARGET_URL}
    [Template]  Should redirect to login
    /players
    /player/1/update
    /cup/new/
    /games/
    /game/1/reactivate

*** Keywords ***
Page status ok
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${false}
    Should be equal as strings  ${resp.status_code}  200

Should redirect to login
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  ${TARGET_URL}/login?

Should redirect to main page
    [Arguments]  ${url}
    ${resp}=  Get Request  local  ${url}  allow_redirects=${true}
    Should be equal as strings  ${resp.status_code}  200
    Should start with  ${resp.url}  ${TARGET_URL}/
