*** Settings ***
Library             SeleniumLibrary
Default Tags        selenium
Suite Teardown      Close All Browsers

*** Variables ***
${MAIN_PAGE_URL}        http://localhost:8887/
${BROWSER}              Chrome

*** Test Cases ***
Play full game with one player
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    Navigate to start a new game
    Select course   Lyhyt rata - 6
    Select player   Club member
    Start game
    Should be on game page

    Mark 1 throws for the first player
    Press publish
    Mark 2 throws for the first player
    Mark 0 approaches and 1 puts for the first player
    Press publish
    Mark 3 throws for the first player
    Mark 1 approaches and 1 puts for the first player
    Press publish
    Mark 4 throws for the first player
    Mark 1 approaches and 2 puts for the first player
    Press publish
    Mark 5 with 1 penalties for the first player
    Press publish

    Press end game
    Dismiss alert that warns about missing results
    Should be on game page

    Mark 6 with 2 penalties for the first player
    Press publish

    Press end game
    Accept alert about ending the game
    Should be on main page

Play full game with new guest player
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    Navigate to add new player
    Type Friend as the new player name
    Submit Form

    Navigate to start a new game
    Select course   Lyhyt rata - 6
    Select player   Club member
    Show non members
    Select player   Friend
    Start game
    Should be on game page

    Mark 3 throws for the first player
    Mark 3 throws for the second player
    Press publish
    Mark 3 throws for the first player
    Mark 4 throws for the second player
    Press publish
    Mark 3 throws for the first player
    Mark 4 throws for the second player
    Press publish
    Mark 3 throws for the first player
    Mark 3 throws for the second player
    Press publish
    Mark 3 throws for the first player
    Mark 5 throws for the second player
    Press publish
    Mark 4 throws for the first player
    Mark 6 throws for the second player
    Press publish

    Press end game
    Accept alert about ending the game
    Should be on main page


*** Keywords ***
Open EsKodb
    Open Browser    ${MAIN_PAGE_URL}    ${BROWSER}

Should be on main page
    Location Should Be  ${MAIN_PAGE_URL}

Should be on game page
    Location Should Contain     ${MAIN_PAGE_URL}game/

Navigate to start a new game
    Click Element    new_game_btn

Navigate to add new player
    Click Element    new_player_btn

Type ${name} as the new player name
    Input Text  name_input  ${name}

Select course
    [Arguments]    ${course_name}
    Select From List By Label  coure_select  ${course_name}

Select player
    [Arguments]    ${player_name}
    Click Element  //label[text() = '${player_name}']

Show non members
    Click Element  non_members_toggle

Start game
    Click Element   start_game_btn

Press publish
    Click Element   publish_btn

Press end game
    Click Element   end_game_btn

Dismiss alert that warns about missing results
    Alert Should Be Present  TULOKSIA PUUTTUU! Haluatko varmasti lopettaa?  action=DISMISS

Accept alert about ending the game
    Alert Should Be Present     Haluatko varmasti lopettaa?


Mark ${result} throws for the first player
    Mark result for player  0  ${result}  0

Mark ${result} throws for the second player
    Mark result for player  1  ${result}  0

Mark ${result} throws for the third player
    Mark result for player  2  ${result}  0

Mark ${result} throws for the fourth player
    Mark result for player  3  ${result}  0

Mark ${result} with ${penalty} penalties for the first player
    Mark result for player  0  ${result}  ${penalty}

Mark ${result} with ${penalty} penalties for the second player
    Mark result for player  1  ${result}  ${penalty}

Mark ${result} with ${penalty} penalties for the third player
    Mark result for player  2  ${result}  ${penalty}

Mark ${result} with ${penalty} penalties for the fourth player
    Mark result for player  3  ${result}  ${penalty}

Mark result for player
    [Arguments]     ${player_index}  ${result}  ${penalty}
    Select From List By Value  throws_${player_index}  ${result}
    Select From List By Value  penalty_${player_index}  ${penalty}

Mark ${approaches} approaches and ${puts} puts for the first player
    Mark approaches and puts for player  0  ${approaches}  ${puts}

Mark ${approaches} approaches and ${puts} puts for the second player
    Mark approaches and puts for player  1  ${approaches}  ${puts}

Mark ${approaches} approaches and ${puts} puts for the third player
    Mark approaches and puts for player  2  ${approaches}  ${puts}

Mark ${approaches} approaches and ${puts} puts for the fourth player
    Mark approaches and puts for player  3  ${approaches}  ${puts}

Mark approaches and puts for player
    [Arguments]     ${player_index}  ${approaches}  ${puts}
    Select From List By Value  approaches_${player_index}  ${approaches}
    Select From List By Value  puts_${player_index}  ${puts}

