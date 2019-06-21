*** Settings ***
Library         REST    ${TARGET_URL}

*** Variables ***
${TARGET_URL}=      http://localhost:8887

*** Test cases ***

Players return valid data
    GET         /data/players/
    Array       $.players
    Integer     $.players[*].id
    String      $.players[*].name
    Boolean     $.players[*].member

# Results return valid data
#     GET         /data/course/1/results/
#     Validate game result data object    $.games[*]



*** Keywords ***

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
