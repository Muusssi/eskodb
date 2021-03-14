*** Settings ***
Library             testutils.py

*** Variables ***
${MAIN_PAGE_URL}        http://localhost:8887/
${BROWSER}              Chrome

*** Keywords ***
Open EsKodb
    Open Browser    ${MAIN_PAGE_URL}    ${BROWSER}

Should be on main page
    Location Should Be  ${MAIN_PAGE_URL}

Should be on game page
    Location Should Contain     ${MAIN_PAGE_URL}game/

Should be on update course page
    Location Should Contain     ${MAIN_PAGE_URL}course/
    Location Should Contain     /update

Should be on reuse holes page
    Location Should Contain     ${MAIN_PAGE_URL}course/
    Location Should Contain     /reuse_holes_from/

Should be on course page for '${course_name}'
    Location Should Contain     ${MAIN_PAGE_URL}course/
    Element Text Should Be      course_name_span  ${course_name}

Should be viewing an uploaded image
    Location Should Contain     ${MAIN_PAGE_URL}data/course_image/
    Element Should Be Visible   tag:img

Navigate to start a new game
    Click Element    new_game_btn

Navigate to add new player
    Click Element    new_player_btn

Navigate to courses page
    Click Element    courses_btn

Type '${name}' as the new player name
    Input Text  name_input  ${name}

Type '${name}' as the new course name
    Input Text  name_input  ${name}

Type '${hole_count}' as the new course hole count
    Input Text  holes_input  ${hole_count}

Update '${par}' as par for the ${index} hole
    ${index}=   parse_index  ${index}
    Input Text  par_input${index}  ${par}

Update '${length}' as length for the ${index} hole
    ${index}=   parse_index  ${index}
    Input Text  length_input${index}  ${length}

Update '${height}' as height for the ${index} hole
    ${index}=   parse_index  ${index}
    Input Text  height_input${index}  ${height}

Select OB area for the ${index} hole
    ${index}=   parse_index  ${index}
    Select Checkbox  ob_area_cb${index}

Unselect OB area for the ${index} hole
    ${index}=   parse_index  ${index}
    Unselect Checkbox  ob_area_cb${index}

Select mando for the ${index} hole
    ${index}=   parse_index  ${index}
    Select Checkbox  mando_cb${index}

Unselect mando for the ${index} hole
    ${index}=   parse_index  ${index}
    Unselect Checkbox  mando_cb${index}

Select gate for the ${index} hole
    ${index}=   parse_index  ${index}
    Select Checkbox  gate_cb${index}

Unselect gate for the ${index} hole
    ${index}=   parse_index  ${index}
    Unselect Checkbox  gate_cb${index}

Select island for the ${index} hole
    ${index}=   parse_index  ${index}
    Select Checkbox  island_cb${index}

Unselect island for the ${index} hole
    ${index}=   parse_index  ${index}
    Unselect Checkbox  island_cb${index}

Hole info should say that ${index} hole has ${feature}
    ${index}=   parse_index  ${index}  1
    Table Cell Should Contain  holes_info  6  ${index}  ${feature}

Hole info should say that total length is
    [Arguments]    ${length}
    Table Cell Should Contain  holes_info  3  -1  ${length}

Hole info should say that total par is
    [Arguments]    ${par}
    Table Cell Should Contain  holes_info  2  -1  ${par}

Hole info should say that ${index} hole par is ${par}
    ${index}=   parse_index  ${index}  1
    Table Cell Should Contain  holes_info  2  ${index}  ${par}

Hole info should say that ${index} hole length is ${length}
    ${index}=   parse_index  ${index}  1
    Table Cell Should Contain  holes_info  3  ${index}  ${length}

Current result for the ${index} player should be ${result}
    ${index}=   parse_index  ${index}  2
    Table Cell Should Contain  results_table  ${index}  -2  ${result}

Current par for the ${index} player should be ${par}
    ${index}=   parse_index  ${index}  2
    Table Cell Should Contain  results_table  ${index}  -1  ${par}

Start new game on the course
    Click Element    play_course_btn

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
    Sleep  0.1

Press end game
    Click Element   end_game_btn

Press new course
    Click Element   new_course_btn

Press update holes
    Click Element   update_holes_btn

Press new layout
    Click Element   new_layout_btn

Press add image
    Click Element   add_image_btn

Dismiss alert that warns about missing results
    Alert Should Be Present  TULOKSIA PUUTTUU! Haluatko varmasti lopettaa?  action=DISMISS

Accept alert about ending the game
    Alert Should Be Present     Haluatko varmasti lopettaa?


Mark ${result} throws for the ${index} player
    ${index}=   parse_index  ${index}  -1
    Mark result for player  ${index}  ${result}  0

Mark ${result} with ${penalty} penalties for the ${index} player
    ${index}=   parse_index  ${index}  -1
    Mark result for player  ${index}  ${result}  ${penalty}

Mark result for player
    [Arguments]     ${player_index}  ${result}  ${penalty}
    Select From List By Value  throws_${player_index}  ${result}
    Select From List By Value  penalty_${player_index}  ${penalty}

Mark ${approaches} approaches and ${puts} puts for the ${index} player
    ${index}=   parse_index  ${index}  -1
    Mark approaches and puts for player  ${index}  ${approaches}  ${puts}

Mark approaches and puts for player
    [Arguments]     ${player_index}  ${approaches}  ${puts}
    Select From List By Value  approaches_${player_index}  ${approaches}
    Select From List By Value  puts_${player_index}  ${puts}

Course list is fully populated
    Table Column Should Contain  course_table  2  A-Rata
    Table Column Should Contain  course_table  2  B-Rata
    Table Column Should Contain  course_table  2  Lyhyt rata

Search course by name
    [Arguments]     ${filter_input}
    ${filter_locator}=  Set Variable  //table[@id="course_table"]//td[2]//input
    Input Text  ${filter_locator}  ${filter_input}

Course list should contain
    [Arguments]     ${course_name}
    Table Column Should Contain  course_table  2  ${course_name}

Course list should not contain
    [Arguments]     ${course_name}
    ${other_course_visible}=  Run Keyword And Return Status
    ...     Table Column Should Contain  course_table  2  ${course_name}
    Should Not Be True  ${other_course_visible}  Course '${course_name}' should not be visible

Clear course name filter
    ${filter_locator}=  Set Variable  //table[@id="course_table"]//td[2]//input
    Clear input with back space  ${filter_locator}
    Course list is fully populated

Clear input with back space
    [Arguments]     ${input_locator}
    Repeat Keyword  0.3s  Press Keys  ${input_locator}  BACKSPACE

Course record should be
    [Arguments]     ${course_record}
    Table Column Should Contain  course_table  8  ${course_record}

Open course page for
    [Arguments]     ${course_name}
    Search course by name  ${course_name}
    Click Element  link:${course_name}
    Should be on course page for '${course_name}'
