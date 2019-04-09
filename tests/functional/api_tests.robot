*** Settings ***
Library         REST    http://localhost:8887

*** Test cases ***

Players return valid data
    GET         /data/players/
    Array       $.players
    Integer     $..id
    String      $..name
    Boolean     $..member

Courses return valid data
    GET         /data/courses/
    Array       $.courses
    Validate course data object     $.courses[*]

Course return valid data
    GET         /data/course/1/
    Validate course data object     $
    Validate holes data object      $.holes_data[*]

Holes return valid data
    GET         /data/course/1/holes/
    Validate holes data object      $.holes[*]

Rule sets return valid data
    GET         /data/course/1/rule_sets/
    Validate rule set data object   $.rule_sets[*]

Results return valid data
    GET         /data/course/1/results/
    Validate game result data object    $.games[*]

Hole returns valid data
    GET         /data/hole/1/
    Validate holes data object  $

# Game times return valid data
#     GET         /data/course/1/game_times/
#     Validate game times data objects    $.0[0]

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

Validate rule set data object
    [Arguments]     ${json_path}
    Object      ${json_path}
    Integer     ${json_path}.id
    String      ${json_path}.name
    String      ${json_path}.description
    Integer     ${json_path}.games

Validate game times data objects
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
