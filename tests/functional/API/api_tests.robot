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
