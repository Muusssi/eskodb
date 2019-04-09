*** Settings ***
Documentation     Simple example using SeleniumLibrary.
Library           SeleniumLibrary
Default Tags      selenium

*** Variables ***
${LOGIN URL}        http://localhost:8887
${BROWSER}          Chrome
${TEST_COURSE_ID}   36
${TEST_PLAYER_ID}   20

*** Test Cases ***
Play full game with one player
    Open EsKodb
    Press new game button
    Select course           ${TEST_COURSE_ID}
    Select players          ${TEST_PLAYER_ID}
    Click Element           start_game_btn
    Mark result for first player  3
    Click Element   publish_btn
    Mark result for first player  3
    Click Element   publish_btn
    Mark result for first player  3
    Click Element   publish_btn
    Mark result for first player  3
    Click Element   publish_btn
    Mark result for first player  3
    Click Element   publish_btn
    Click Element   previous_btn
    Click Element   previous_btn
    Mark result for first player  4
    Click Element   publish_btn
    Click Element   continue_btn
    Mark result for first player  3
    Click Element   publish_btn
    Click Element   end_game_btn
    Alert Should Be Present
    Close Browser

*** Keywords ***
Open EsKodb
    Open Browser    ${LOGIN URL}    ${BROWSER}

Press new game button
    Click Element    new_game_btn

Select course
    [Arguments]    ${course_id}
    Select From List By Value  coure_select  ${course_id}

Select players
    [Arguments]    ${player_id}
    Click Element    cb_${player_id}

Press publish
    Click Element   publish_btn

Mark result for first player
    [Arguments]    ${result}
    Select From List By Value  throws_0  ${result}

