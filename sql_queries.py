
def holes_of_course(course_id):
    return """
SELECT hole
FROM hole_mapping
WHERE course={course_id} ORDER BY hole_number
""".format(course_id=int(course_id))

def game_results(game_id):
    return """
SELECT result.id, result.player,
    result.throws, result.penalty, result.approaches, result.puts
FROM result
JOIN hole_mapping ON result.hole=hole_mapping.hole
JOIN player ON player.id=result.player
WHERE result.game={game_id}
ORDER BY player.name, hole_mapping.hole_number
""".format(game_id=int(game_id))

def previous_hole_results(game_id, special_rules):
    return """
SELECT player.name, hole_number, avg(throws), min(throws)
FROM result
JOIN player ON result.player=player.id
JOIN game ON result.game=game.id
JOIN hole_mapping ON result.hole=hole_mapping.hole
WHERE result.hole IN (
    SELECT DISTINCT hole
    FROM hole_mapping
    JOIN game ON hole_mapping.course=game.course
    WHERE game={game_id}
) AND game.special_rules{special_rules_filter}
  AND result.player IN (SELECT DISTINCT player FROM result WHERE game={game_id})
GROUP BY player.name, hole_number
ORDER BY player.name, hole_number""".format(
        game_id=int(game_id),
        special_rules_filter="={}".format(int(special_rules)) if special_rules else " IS NULL",
    )

def previous_hole_stats(game_id, special_rules):
    return """
SELECT player.name, hole_number, result.hole, avg(throws), min(throws), count(throws)
FROM hole
JOIN hole_mapping ON hole.id=hole_mapping.hole
JOIN result ON result.hole=hole.id
JOIN player ON result.player=player.id
JOIN game ON result.game=game.id
WHERE hole.id IN (
    SELECT DISTINCT hole
    FROM hole_mapping
    JOIN game ON game.course=hole_mapping.course
    WHERE game.id={game_id}
) AND game.special_rules{special_rules_filter}
  AND game.active=false
GROUP BY player.name, hole_number, result.hole
ORDER BY player.name, hole_number
""".format(
        game_id=int(game_id),
        special_rules_filter="={}".format(int(special_rules)) if special_rules else " IS NULL",
    )

def game_times(course_id):
    return """
SELECT size, rules, count(*), min(game_time), avg(game_time), max(game_time), name
FROM (
    SELECT game.id, count(*) as size, end_time - start_time as game_time,
           (CASE WHEN game.special_rules IS NULL THEN 0 ELSE game.special_rules END) as rules,
           (CASE WHEN game.special_rules IS NULL THEN 'Standard' ELSE name END) as name
    FROM result
    JOIN hole_mapping ON result.hole=hole_mapping.hole
    JOIN game ON game.id=result.game
    LEFT OUTER JOIN special_rules ON game.special_rules=special_rules.id
    WHERE game.course={course_id}
        AND NOT game.unfinished
        AND end_time IS NOT NULL
        AND hole_mapping.course={course_id}
        AND hole_mapping.hole_number=1
    GROUP BY game.id, name
) AS games
GROUP BY name, rules, size
ORDER BY name, rules, size""".format(course_id=int(course_id))

COURSE_PARS = """
SELECT course, sum(par) as sum
FROM hole
JOIN hole_mapping ON hole_mapping.hole=hole.id
GROUP BY course
"""

LATEST_GAMES = """
SELECT start_time, game_of_day, course_name, course_id, player_name, player_id, res, par
FROM (
    SELECT game.start_time, game.game_of_day, course.name as course_name, course.id as course_id,
           player.name as player_name, player.id as player_id,
           sum(result.throws) as res, sum(result.throws) - pars.sum as par,
           count(nullif(throws IS NULL, false)) as partial
    FROM result
    JOIN game ON result.game=game.id
    JOIN player ON player.id=result.player
    JOIN course ON game.course=course.id
    JOIN ({course_pars}) as pars ON pars.course=course.id
    WHERE game.start_time > (date 'today' -100) AND game.active=false
    GROUP BY game.start_time, game.game_of_day, course.name, course.id, player.name, player.id, pars.sum
    ORDER BY game.start_time DESC, game.game_of_day DESC
) AS latest_results WHERE partial=0
""".format(course_pars=COURSE_PARS)

ACTIVE_RESULTS = """
SELECT game.start_time, game.game_of_day, game.id, course.name, player.name,
       sum(result.throws) as res, sum(result.throws - par) as par, count(throws), course.holes
FROM result
JOIN hole ON result.hole=hole.id
JOIN game ON result.game=game.id
JOIN player ON player.id=result.player
JOIN course ON course.id=game.course
WHERE game.active=true
GROUP BY game.start_time, game.game_of_day, game.id, course.name, course.id, player.name
"""

COURSE_BESTS = """
SELECT totals.course, totals.player, min(totals.res) as best,
       EXTRACT(year FROM totals.start_time) as season
FROM (
    SELECT game.course, result.player, game.start_time, game.game_of_day, sum(result.throws) as res,
           count(nullif(throws IS NULL, false)) as partial
    FROM result
    JOIN game ON game.id=result.game
    WHERE active=false AND special_rules IS NULL
    GROUP BY game.course, result.player, game.start_time, game.game_of_day
    ORDER BY game.course, result.player, res DESC
) as totals
WHERE partial=0
GROUP BY course, player, season
ORDER BY course, player, season;
"""

CUP_RESULTS_2017 = """
SELECT cup, player, cup_results.course, game, LEAST(cup_max, summa-pars.sum) as res, time
FROM ({course_pars}) as pars
JOIN (
    SELECT DISTINCT ON (cup, player) cup, player, course, game, cup_max, summa, time
    FROM (
        SELECT cup.id as cup, player.id as player, course.id as course, game.id as game,
               cup.max_par as cup_max, sum(throws) as summa, game.start_time as time
        FROM course
        JOIN cup ON cup.course=course.id
        JOIN game ON game.course=course.id
         AND EXTRACT(year FROM game.start_time)=cup.year
         AND EXTRACT(month FROM game.start_time)=cup.month
        JOIN result ON result.game=game.id
        JOIN player ON result.player=player.id
        JOIN membership ON membership.player=result.player AND membership.year=2017
        WHERE game.unfinished=false AND game.active=false
        GROUP BY cup.id, player.id, course.id, game.id, cup.max_par
        ORDER BY course.name, summa
    ) as results
    ORDER BY cup, player, summa
) as cup_results ON cup_results.course=pars.course
ORDER BY cup, res
""".format(course_pars=COURSE_PARS)

EXCLUDED_HOLES = {2021: ['47']}

def cup_results_query(year, begin_date, end_date):
    excluded_holes_filter = None
    if int(year) in EXCLUDED_HOLES:
        excluded_holes_filter = 'AND hole.id NOT IN ({})'.format(','.join(EXCLUDED_HOLES[year]))
    return """
SELECT * FROM (
    SELECT DISTINCT ON (player, course) player, course, res, start_time::date
    FROM (
        SELECT sum(throws - hole.par) as res, result.player, game.course, game.start_time,
                count(nullif(throws IS NULL, false)) as unfinished
        FROM result
        JOIN hole ON hole.id=result.hole
        JOIN game ON game.id=result.game
        JOIN membership ON membership.player=result.player AND membership.year={year}
        WHERE game.course IN (SELECT course FROM eskocup_course WHERE year={year})
          AND game.start_time >= '{begin_date}'
          AND game.start_time <= '{end_date}'
          AND game.special_rules IS NULL
            {excluded_holes_filter}
        GROUP BY result.player, game.id, game.course
        ORDER BY game.course, res DESC
    ) as results
    WHERE results.unfinished=0
    ORDER BY player, course, res
) AS cup_results
ORDER BY course, res
""".format(year=int(year),
           begin_date=begin_date,
           end_date=end_date,
           excluded_holes_filter=excluded_holes_filter if excluded_holes_filter else '')

COMPETITION_EVENTS_QUERY = """
SELECT competition.id, course.id, course.name, start_time, end_time, rounds,
       (start_time<now() AND end_time>now()) as active, sum(par) as par
FROM competition
JOIN course ON course.id=competition.course
JOIN hole_mapping ON hole_mapping.course=course.id
JOIN hole ON hole.id=hole_mapping.hole
WHERE competition=%s
GROUP BY competition.id, course.id, course.name, start_time, end_time, rounds
ORDER BY start_time;
"""

COMPETITION_RESULTS = """
SELECT competition_id, player_id, player_name, game_date, result, attempts
FROM (
    SELECT DISTINCT ON (competition_id, player.id)
           competition_id, player_id, player.name as player_name, result, attempts,
           game.start_time::date as game_date
    FROM (
        SELECT registration.competition as competition_id,
               registration.player as player_id,
               registration.game as game_id,
               sum(throws) as result,
               sum(CASE WHEN throws IS NULL THEN 1 ELSE 0 END) as missing_results,
               count(*) OVER (PARTITION BY registration.competition, registration.player) as attempts
        FROM result
        JOIN competition_registration as registration ON result.game=registration.game
                                                     AND result.player=registration.player
        JOIN competition ON registration.competition=competition.id
        WHERE competition.competition=%s
        GROUP BY registration.competition, registration.player, registration.game
    ) AS raw_results
    JOIN player ON player.id=player_id
    JOIN game ON game.id=game_id
    WHERE missing_results=0
    ORDER BY competition_id, player.id, result
) as results
ORDER BY competition_id, result;
"""

def player_stats(player_id):
    return """
SELECT course.id, course.name, course.holes, course.version,
       pars.sum, count, best.start_time::date, throws, throws - pars.sum
FROM course
JOIN (
    SELECT DISTINCT ON (course) course, throws, start_time
    FROM (
        SELECT course, sum(throws) as throws, start_time,
               count(nullif(throws IS NULL, false)) as incomplete
        FROM result
        JOIN game ON game.id=result.game
        WHERE result.player={player_id}
        GROUP BY game.id
    ) AS results
    WHERE incomplete=0
    ORDER BY course, throws
) AS best ON course.id=best.course
JOIN ({course_pars}) AS pars ON pars.course=course.id
JOIN (
    SELECT course, count(*) FROM (
        SELECT course, game.id,
            count(nullif(throws IS NULL, false)) as incomplete
        FROM game
        JOIN result ON game.id=result.game
        WHERE result.player={player_id}
        GROUP BY course, game.id
    ) AS games
    WHERE incomplete=0 GROUP BY course
) AS game_count ON game_count.course=course.id
ORDER BY course.name, course.version;
""".format(player_id=int(player_id), course_pars=COURSE_PARS)

COURSES_DATA = """
SELECT course.id, name, official_name, holes, version, course.description, town, sum(esko_rating),
       sum(length) as length, avg(length), max(length), min(length),
       sum(par) as par, avg(par), max(par), min(par), playable
FROM course
JOIN hole_mapping ON hole_mapping.course=course.id
JOIN hole ON hole.id=hole_mapping.hole
GROUP BY course.id, name, official_name, holes, version, course.description, town
ORDER BY name, holes, version
"""

def course_data(course_id):
    return """
SELECT course.id, name, official_name, holes, version, course.description, town,
       sum(esko_rating) as esko_rating, sum(length) as length, avg(length) as avg_length,
       max(length) as max_length, min(length) as min_length,
       sum(par) as par, avg(par) as avg_apr, max(par) as max_par, min(par) as min_par, playable
FROM course
JOIN hole_mapping ON hole_mapping.course=course.id
JOIN hole ON hole.id=hole_mapping.hole
WHERE course.id={course_id}
GROUP BY course.id, name, official_name, holes, version, course.description, town
ORDER BY name, holes, version
""".format(course_id=int(course_id))

def course_images_info(course_id):
    return """
SELECT id, description, timestamp
FROM course_image
WHERE course={course_id}
ORDER BY timestamp DESC
""".format(course_id=int(course_id))

def holes_data(course_id):
    return """
SELECT hole.id, course, hole_number, description, par,
       length, height, elevation, hole.type, hole_terrain,
       ob_area, mando, gate, island, esko_rating, count(*)
FROM hole
JOIN hole_mapping ON hole.id=hole_mapping.hole
LEFT OUTER JOIN hole_map_item ON hole.id=hole_map_item.hole
WHERE course={course_id}
GROUP BY hole.id, course, hole_number, description, par,
    length, height, elevation, hole.type, hole_terrain,
    ob_area, mando, gate, island, esko_rating
ORDER BY hole_number
""".format(course_id=int(course_id))

def hole_data(hole_id):
    return """
SELECT hole.id, hole.description, par,
       length, height, elevation, type, hole_terrain,
       ob_area, mando, gate, island, esko_rating,
       course.id, hole_number, course.name, course.holes, course.version
FROM hole
JOIN hole_mapping ON hole_mapping.hole=hole.id
JOIN course ON hole_mapping.course=course.id
WHERE hole.id={hole_id} AND hole_mapping.hole={hole_id}
ORDER BY version DESC
""".format(hole_id=int(hole_id))

def hole_image_data_for_course(course_id):
    return """
SELECT id, hole_image.hole, hole_number, description, timestamp
FROM hole_image
JOIN hole_mapping ON hole_image.hole=hole_mapping.hole
WHERE hole_mapping.course={course_id}
ORDER BY hole_number, timestamp DESC
""".format(course_id=int(course_id))

BESTS_OF_COURSES = """
SELECT DISTINCT ON (course) course, res, name, player_id, start_time::date
FROM (
    SELECT game.course, game.start_time, player.name, player.id as player_id,
        sum(throws - par) as res,
        count(nullif(throws IS NULL, false)) as incomplete
    FROM result
    JOIN game ON game.id=result.game
    JOIN hole ON hole.id=result.hole
    JOIN player ON player.id=result.player
    WHERE game.special_rules IS NULL
    GROUP BY game.id, player.name, player.id
) AS results
WHERE incomplete=0
ORDER BY course, res, start_time
"""

def course_bests(course_id):
    return """
SELECT DISTINCT ON (rules, season) season, rules, res, name, player_id, start_time::date
FROM (
    SELECT game.start_time, player.name, player.id as player_id,
        EXTRACT(year FROM start_time) as season, sum(throws - par) as res,
        (CASE WHEN special_rules IS NULL THEN 0 ELSE special_rules END) as rules,
        count(nullif(throws IS NULL, false)) as incomplete
    FROM result
    JOIN game ON game.id=result.game
    JOIN hole ON hole.id=result.hole
    JOIN player ON player.id=result.player
    WHERE game.course={course_id}
    GROUP BY game.id, player.name, player.id
) AS results
WHERE incomplete=0
ORDER BY rules, season, res, start_time
""".format(course_id=int(course_id))

def course_results(course_id):
    return """
SELECT game.id as game_id, game.start_time, game.end_time, game_of_day, game.special_rules,
    player.id as player_id, player.name, player.member,
    result.id as result_id, result.hole as hole_id, throws, penalty,
    approaches, puts, reported_at, hole_number as hole_num
FROM result
JOIN game ON game.id=result.game
JOIN hole ON hole.id=result.hole
JOIN hole_mapping ON result.hole=hole_mapping.hole
JOIN player ON player.id=result.player
WHERE game.course={course_id}
  AND hole_mapping.course={course_id}
  AND NOT game.active
ORDER BY game.start_time DESC, game_of_day DESC, name, hole_number
""".format(course_id=int(course_id))

HOLE_ESKO_RATINGS = """
SELECT course, hole_number, esko_rating
FROM hole
JOIN hole_mapping ON result.hole=hole_mapping.hole
ORDER BY course, hole
"""

UPDATE_RESULT = """
UPDATE result
SET throws=%s, penalty=%s, approaches=%s, puts=%s, reported_at='now'
WHERE id=%s
"""

def game_results(game_id):
    return """
SELECT result.id, player.id, player.name, hole.id, hole_number,
       throws, penalty, approaches, puts, reported_at
FROM result
JOIN game ON result.game=game.id
JOIN hole ON hole.id=result.hole
JOIN hole_mapping ON hole.id=hole_mapping.hole
                 AND hole_mapping.course=game.course
JOIN player ON player.id=result.player
WHERE result.game={game_id}
ORDER BY player.name, hole_number
""".format(game_id=int(game_id))

def merge_hole_results(course1, hole1, course2, hole2):
    return """
UPDATE result SET hole=(SELECT hole
                        FROM hole_mapping
                        WHERE course={course1_id}
                          AND hole_number={hole_1})
WHERE hole=(SELECT hole
            FROM hole_mapping
            WHERE course={course2_id} AND hole_number={hole_2})
""".format(course1_id=int(course1),
           course2_id=int(course2),
           hole_1=int(hole1),
           hole_2=int(hole2))

def merge_holes(course1, hole1, course2, hole2):
    return """
UPDATE hole_mapping SET hole=(SELECT hole
                              FROM hole_mapping
                              WHERE course={course1_id}
                                AND hole_number={hole_1})
WHERE course={course2_id} AND hole_number={hole_2}
""".format(course1_id=int(course1),
           course2_id=int(course2),
           hole_1=int(hole1),
           hole_2=int(hole2))

def move_results(game_id, old_course, new_course, hole):
    return """
UPDATE result SET hole=(SELECT hole
                        FROM hole_mapping
                        WHERE course={new_course}
                          AND hole_number={hole_number})
WHERE hole=(SELECT hole
            FROM hole_mapping
            WHERE course={old_course}
              AND hole_number={hole_number})
  AND game={game_id}
""".format(game_id=int(game_id),
           old_course=int(old_course),
           new_course=int(new_course),
           hole_number=int(hole))

if __name__ == '__main__':
    print(previous_hole_stats(888, 1))

