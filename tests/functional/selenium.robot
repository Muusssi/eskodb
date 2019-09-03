*** Settings ***
Library             SeleniumLibrary
Force Tags          selenium
Suite Teardown      Close All Browsers
Resource            selenium_keywords.robot

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
    Type 'Friend' as the new player name
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

    Navigate to courses page
    Search course by name  Lyhyt
    Course record should be  Club member (1)

Create a new course and play round
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    Navigate to courses page
    Press new course
    Type 'New course' as the new course name
    Type '4' as the new course hole count
    Submit Form
    Should be on update course page

    Update '2' as par for the first hole
    Update '45' as length for the first hole
    Update '0' as height for the first hole
    Select OB area for the first hole

    Update '4' as par for the second hole
    Update '150' as length for the second hole
    Update '-5' as height for the second hole
    Select mando for the second hole

    Update '5' as par for the third hole
    Update '184' as length for the third hole
    Select island for the third hole

    Update '4' as par for the 4th hole
    Update '145' as length for the 4th hole
    Update '8' as height for the 4th hole
    Select gate for the 4th hole

    Submit Form
    Should be on course page for 'New course'
    Hole info should say that first hole par is 2
    Hole info should say that first hole length is 45
    Hole info should say that second hole par is 4
    Hole info should say that second hole length is 150
    Hole info should say that third hole par is 5
    Hole info should say that third hole length is 184
    Hole info should say that 4th hole par is 4
    Hole info should say that 4th hole length is 145
    Hole info should say that first hole has ob
    Hole info should say that second hole has mando
    Hole info should say that third hole has island
    Hole info should say that 4th hole has gate
    Hole info should say that total length is  524
    Hole info should say that total par is  15

    Start new game on the course
    Select player  Club member
    Start game
    Should be on game page

    Mark 3 throws for the first player
    Press publish
    Current result for the first player should be 3
    Current par for the first player should be 1
    Mark 3 throws for the first player
    Press publish
    Current result for the first player should be 6
    Current par for the first player should be 0
    Mark 4 throws for the first player
    Press publish
    Current result for the first player should be 10
    Current par for the first player should be -1
    Mark 5 with 1 penalties for the first player
    Press publish
    Current result for the first player should be 15
    Current par for the first player should be 0

    Press end game
    Accept alert about ending the game
    Should be on main page

Browse the courses list
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    Navigate to courses page
    Course list is fully populated
    Search course by name  A-
    Course list should contain  A-Rata
    Course list should not contain  B-Rata
    Search course by name  B-
    Course list should contain  B-Rata
    Course list should not contain  A-Rata
    Clear course name filter

Edit a course
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    Navigate to courses page
    Open course page for  B-Rata
    Press update holes

    Update '2' as par for the first hole
    Update '45' as length for the first hole
    Update '0' as height for the first hole
    Select OB area for the first hole

    Update '4' as par for the second hole
    Update '150' as length for the second hole
    Update '-5' as height for the second hole
    Select mando for the second hole

    Update '5' as par for the third hole
    Update '184' as length for the third hole
    Select island for the third hole

    Update '4' as par for the 4th hole
    Update '145' as length for the 4th hole
    Update '8' as height for the 4th hole
    Select gate for the 4th hole

    Update '3' as par for the 5th hole
    Update '90' as length for the 5th hole
    Update '3' as par for the 6th hole
    Update '90' as length for the 6th hole
    Update '3' as par for the 7th hole
    Update '90' as length for the 7th hole
    Update '3' as par for the 8th hole
    Update '90' as length for the 8th hole
    Update '3' as par for the 9th hole
    Update '90' as length for the 9th hole
    Update '3' as par for the 10th hole
    Update '90' as length for the 10th hole
    Update '3' as par for the 11th hole
    Update '90' as length for the 11th hole
    Update '3' as par for the 12th hole
    Update '90' as length for the 12th hole

    Submit Form
    Should be on course page for 'B-Rata'
    Hole info should say that first hole par is 2
    Hole info should say that first hole length is 45
    Hole info should say that second hole par is 4
    Hole info should say that second hole length is 150
    Hole info should say that third hole par is 5
    Hole info should say that third hole length is 184
    Hole info should say that 4th hole par is 4
    Hole info should say that 4th hole length is 145
    Hole info should say that first hole has ob
    Hole info should say that second hole has mando
    Hole info should say that third hole has island
    Hole info should say that 4th hole has gate
    Hole info should say that total length is  1244
    Hole info should say that total par is  39

Upload an image linked to course
    [Setup]         Open EsKodb
    [Teardown]      Close Browser
    [Tags]          new
    Navigate to courses page
    Open course page for  A-Rata
    Press add image

    Choose File     file_input  ${CURDIR}/course_map.jpg
    Submit Form
    Should be on course page for 'A-Rata'

    Click Element  link:Ratakartta
    Switch Window  NEW
    Should be viewing an uploaded image
    Close Window
    Switch Window  MAIN
    Should be on course page for 'A-Rata'

