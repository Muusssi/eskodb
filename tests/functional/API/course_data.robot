*** Settings ***
Library         REST    ${TARGET_URL}

*** Variables ***
${TARGET_URL}=      http://localhost:8887

*** Test cases ***

Courses return valid data
    GET         /data/courses/
    Array       $.courses
    Validate course data object     $.courses[*]

Course return valid data
    GET         /data/course/1/
    Validate course data object     $
    Validate holes data object      $.holes_data[*]

Holes of course return valid data
    GET         /data/course/1/holes/
    Validate holes data object      $.holes[*]

Rule sets of course return valid data
    GET         /data/course/1/rule_sets/
    Validate rule set data object   $.rule_sets[*]

Hole returns valid data
    GET         /data/hole/1/
    Validate hole data object  $

Course game times return valid data
    GET         /data/course/1/game_times/
    Object      $.rules[*]
    Integer     $.rules[*].id
    String      $.rules[*].name
    Validate game times data object    $.rules[*].times[*]

*** Keywords ***

Validate course data object
    [Arguments]     ${json_path}
    Object      ${json_path}
    Integer     ${json_path}.id
    String      ${json_path}.name
    Integer     ${json_path}.holes
    Integer     ${json_path}.par
    Integer     ${json_path}.min_par
    Number      ${json_path}.avg_par
    Integer     ${json_path}.max_par
    Boolean     ${json_path}.playable
    String      ${json_path}.version

Validate holes data object
    [Arguments]     ${json_path}
    Object      ${json_path}
    Integer     ${json_path}.course
    Integer     ${json_path}.hole
    Integer     ${json_path}.id
    Integer     ${json_path}.par
    Boolean     ${json_path}.island
    Boolean     ${json_path}.mando
    Boolean     ${json_path}.ob_area
    Boolean     ${json_path}.island

Validate hole data object
    [Arguments]     ${json_path}
    Object      ${json_path}
    Integer     ${json_path}.id
    Integer     ${json_path}.par
    Boolean     ${json_path}.island
    Boolean     ${json_path}.mando
    Boolean     ${json_path}.ob_area
    Boolean     ${json_path}.island
    Array       ${json_path}.included_in_courses
    Object      ${json_path}.included_in_courses[*]
    Integer     ${json_path}.included_in_courses[*].id
    String      ${json_path}.included_in_courses[*].name
    String      ${json_path}.included_in_courses[*].version
    Integer     ${json_path}.included_in_courses[*].holes
    Integer     ${json_path}.included_in_courses[*].hole_number

Validate rule set data object
    [Arguments]     ${json_path}
    Object      ${json_path}
    Integer     ${json_path}.id
    String      ${json_path}.name
    String      ${json_path}.description
    Integer     ${json_path}.games

Validate game times data object
    [Arguments]     ${json_path}
    String      ${json_path}.min
    String      ${json_path}.avg
    String      ${json_path}.max
    Integer     ${json_path}.pool
    Integer     ${json_path}.games

Validate game result data object
    [Arguments]     ${json_path}
    Integer     ${json_path}.id
    Integer     ${json_path}.game_of_day
    String      ${json_path}.start_time
    Array       ${json_path}.players
    Object      ${json_path}.players[*]
    Integer     ${json_path}.players[*].id
    String      ${json_path}.players[*].name
    Boolean     ${json_path}.players[*].member
    Boolean     ${json_path}.players[*].full
    Array       ${json_path}.players[*].results
    Object      ${json_path}.players[*].results[*]
    Integer     ${json_path}.players[*].results[*].id
    Integer     ${json_path}.players[*].results[*].hole
    Integer     ${json_path}.players[*].results[*].hole_num
    Integer     ${json_path}.players[*].results[*].throws
    Integer     ${json_path}.players[*].results[*].penalty
    String      ${json_path}.players[*].results[*].reported_at
