import psycopg2
import datetime
from collections import defaultdict
import json

GAME_TEMPLATE = "%s #%s"

def cup_results_query(year, first_month, last_month):
    return """
            SELECT DISTINCT ON (player, course) player, course, res, start_time::date
            FROM (
                SELECT sum(throws - hole.par) as res, result.player, game.course, game.start_time,
                        count(nullif(throws IS NULL, false)) as unfinished
                FROM result
                JOIN hole ON hole.id=result.hole
                JOIN game ON game.id=result.game
                WHERE game.course IN (SELECT course FROM eskocup_course WHERE year={year})
                  AND EXTRACT(month FROM game.start_time) >= {first_month}
                  AND EXTRACT(month FROM game.start_time) <= {last_month}
                  AND EXTRACT(year FROM game.start_time) = {year}
                GROUP BY player, game.id, game.course
                ORDER BY player, game.course, res DESC
            ) as results
            WHERE results.unfinished=0
            ORDER BY player, course, res;""".format(
                first_month=int(first_month),
                last_month=int(last_month),
                year=int(year),
            )

def datetime_to_hour_minutes(dt):
    return str(dt).split('.')[0][:-3]

class Database(object):

    def __init__(self, database, host, user, password):
        self._database_user = user
        self._password = password
        self._database_name = database
        self._database_host = host
        self._connect()


    def _connect(self):
        self._conn = psycopg2.connect(
                dbname=self._database_name,
                user=self._database_user,
                password=self._password,
                host=self._database_host,
            )
        self._conn.autocommit = True

    def _cursor(self):
        return self._conn.cursor()

    def _close_connection(self):
        self._conn.close()

    def reconnect(self):
        self._close_connection()
        self._connect()

    def terrains(self):
        sql = "SELECT unnest(enum_range(NULL::terrain));"
        cursor = self._cursor()
        cursor.execute(sql)
        terrain_list = []
        for (terrain, ) in cursor.fetchall():
            terrain_list.append(terrain)
        cursor.close()
        return terrain_list

    def hole_types(self):
        sql = "SELECT unnest(enum_range(NULL::hole_type));"
        cursor = self._cursor()
        cursor.execute(sql)
        type_list = []
        for (hole_type, ) in cursor.fetchall():
            type_list.append(hole_type)
        cursor.close()
        return type_list

    def playable_courses_data(self, fields):
        sql = ("SELECT * FROM (SELECT DISTINCT ON (name) %s FROM course ORDER BY name, version desc) "
               "as playable ORDER BY playable.name") % (
                ','.join([field for field in fields])
            )
        cursor = self._cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        cursor.close()
        return res

    def next_game_of_day(self, course_id):
        sql = "SELECT max(game_of_day) FROM game WHERE course=%s AND start_time::date='today'" % course_id
        cursor = self._cursor()
        cursor.execute(sql, course_id)
        (res, ) = cursor.fetchone()
        if res:
            next_game_of_day = int(res)+1
        else:
            next_game_of_day = 1
        cursor.close()
        return next_game_of_day

    def activate_players(self, player_ids, game_id):
        sql = "UPDATE player SET active=%s WHERE id IN %s"
        cursor = self._cursor()
        cursor.execute(sql, (game_id, tuple(player_ids)))
        cursor.close()

    def next_hole(self, game_id):
        sql = ("SELECT max(hole.hole) FROM result JOIN hole ON result.hole=hole.id "
                "WHERE game=%s AND result.throws IS NOT NULL")
        cursor = self._cursor()
        cursor.execute(sql, (game_id, ))
        (res, ) = cursor.fetchone()
        if res:
            hole = int(res)+1
        else:
            hole = 1
        cursor.close()
        return hole

    def fetch_rows(self, table, fields, criteria={}, order_by="", join_rule="", additional_where=""):
        sql = "SELECT %s FROM %s" % (','.join(['%s.%s' % (table, col) for col in fields]), table)
        if join_rule:
            sql += join_rule
        if criteria or additional_where:
            sql += " WHERE "
            if criteria:
                sql += ' AND '.join(['%s=%s' % (col, '%s') for col in criteria])
            if additional_where:
                if criteria:
                    sql += ' AND '
                sql += additional_where
        if order_by:
            sql += " ORDER BY %s" % order_by
        cursor = self._cursor()
        cursor.execute(sql, criteria.values())
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def update_row(self, table, values, row_id):
        sql = "UPDATE %s SET %s WHERE id=%s " % (table, ','.join(['%s=%s' % (col, '%s') for col in values]), row_id)
        cursor = self._cursor()
        cursor.execute(sql, values.values())
        cursor.close()


    def insert_row(self, table, values):
        sql = "INSERT INTO %s(%s) VALUES (%s) RETURNING id" % (
                table, ','.join([col for col in values]), ','.join(['%s' for col in values])
            )
        cursor = self._cursor()
        cursor.execute(sql, values.values())
        (row_id, ) = cursor.fetchone()
        cursor.close()
        return row_id

    def generate_empty_results(self, game, player_ids):
        cursor = self._cursor()
        sql = "SELECT id FROM hole WHERE course=%s ORDER BY hole"
        cursor.execute(sql, (game.course, ))
        hole_ids = []
        for (hole_id, ) in cursor.fetchall():
            hole_ids.append(hole_id)

        sql = "INSERT INTO result(game, player, hole,reported_at) VALUES %s"
        values = []
        for player_id in player_ids:
            for hole_id in hole_ids:
                values.append("(%s,'%s',%s,null)" % (game.id, player_id, hole_id))
        sql = sql % ','.join(values)
        cursor.execute(sql)
        cursor.close()

    def game_results(self, game_id):
        cursor = self._cursor()
        sql = ("SELECT result.id, result.player, result.throws, result.penalty, result.approaches, result.puts "
                "FROM result JOIN hole on hole.id=result.hole JOIN player ON player.id=result.player "
                "WHERE result.game=%s ORDER BY player.name, hole.hole")
        cursor.execute(sql, (game_id, ))
        result_table = []
        row = []
        current_player = None
        for result_id, player, throws, penalty, approaches, puts in cursor.fetchall():
            if not current_player:
                current_player = player
            if current_player != player:
                result_table.append(row)
                row = []
                current_player = player
            row.append([throws, penalty, approaches, puts, result_id])
        if row:
            result_table.append(row)
        cursor.close()
        return result_table

    def previous_hole_results(self, game_id, special_rules=None):
        cursor = self._cursor()
        if special_rules == None:
            special_rules_filter = "AND game.special_rules IS NULL "
        else:
            special_rules_filter = "AND game.special_rules={rule_id} ".format(rule_id=special_rules)
        sql = ("SELECT player.name, hole.hole, avg(throws), min(throws) "
                "FROM result JOIN game ON result.game=game.id "
                "JOIN hole ON result.hole=hole.id JOIN player ON result.player=player.id "
                "WHERE game.course IN (SELECT course FROM game WHERE id={game_id}) "
                "{special_rules_filter} "
                "AND result.player IN (SELECT player FROM result WHERE game={game_id}) "
                "GROUP BY player.name, hole.hole ORDER BY player.name, hole.hole;").format(
                game_id=game_id,
                special_rules_filter=special_rules_filter,
            )
        cursor.execute(sql)
        result_table = []
        row = []
        current_player = None
        for player, hole, avg, minimum in cursor.fetchall():
            if not current_player:
                current_player = player
            if current_player != player:
                result_table.append(row)
                row = []
                current_player = player
            row.append([float(avg) if avg else None, minimum])
        if row:
            result_table.append(row)
        cursor.close()
        return result_table

    def course_name_dict(self):
        sql = "SELECT name, holes, id FROM course"
        cursor = self._cursor()
        cursor.execute(sql)
        name_dict = {}
        for name, holes, course_id in cursor.fetchall():
            name_dict[course_id] = '%s %s' % (name, holes)
        cursor.close()
        return name_dict

    def game_times_data(self, course_id):
        sql = """SELECT size, rules, count(*), min(game_time), avg(game_time), max(game_time)
                FROM (
                    SELECT game.id, count(*) as size, end_time - start_time as game_time,
                        (CASE WHEN special_rules IS NULL THEN 0 ELSE special_rules END) as rules
                    FROM result JOIN game ON game.id=result.game JOIN hole ON hole.id=result.hole
                    WHERE game.course={course_id} AND NOT game.unfinished AND hole.hole=1 AND end_time IS NOT NULL
                    GROUP BY game.id
                ) AS games GROUP BY rules, size ORDER BY rules, size""".format(course_id=int(course_id))
        cursor = self._cursor()
        cursor.execute(sql)
        game_times = {}
        for size, rules, games, min_time, avg_time, max_time in cursor.fetchall():
            times = {
                    'pool': size, 'games': games, 'min': datetime_to_hour_minutes(min_time),
                    'avg': datetime_to_hour_minutes(avg_time), 'max': datetime_to_hour_minutes(max_time),
                }
            if rules in game_times:
                game_times[rules].append(times)
            else:
                game_times[rules] = [times]
        return game_times

    def player_with_games_on_course(self, course_id):
        sql = ("SELECT distinct player.name, player.id "
                "FROM player JOIN result ON player.id=result.player JOIN game ON result.game=game.id "
                "WHERE game.course=%s")
        cursor = self._cursor()
        cursor.execute(sql, (course_id, ))
        players = []
        for name, player_id in cursor.fetchall():
            players.append((name, player_id))
        cursor.close()
        return players

    def reactivate_game(self, game_id):
        sql = ("UPDATE game SET active=true WHERE id=%s")
        cursor = self._cursor()
        cursor.execute(sql, (game_id, ))
        sql = ("UPDATE player SET active=%s WHERE id IN "
            "(SELECT DISTINCT player FROM result WHERE game=%s)")
        cursor.execute(sql, (game_id, game_id))
        cursor.close()


    def get_latest_games(self):
        query = ("SELECT start_time, game_of_day, course_name, course_id, player_name, player_id, res, par "
                "FROM (SELECT game.start_time, game.game_of_day, course.name as course_name, course.id as course_id, "
                "player.name as player_name, player.id as player_id, "
                "sum(result.throws) as res, sum(result.throws) - pars.sum as par, "
                "count(nullif(throws IS NULL, false)) as partial "
                "FROM result JOIN game ON result.game=game.id JOIN player ON player.id=result.player "
                "JOIN course ON game.course=course.id JOIN ( "
                    "SELECT course.id as course, sum(par) as sum "
                    "FROM hole JOIN course ON hole.course=course.id "
                    "GROUP BY course.id "
                ") as pars ON pars.course=course.id "
                "WHERE game.start_time > (date 'today' -14) AND game.active=false "
                "GROUP BY game.start_time, game.game_of_day, course.name, course.id, player.name, player.id, pars.sum "
                "ORDER BY game.start_time desc, game.game_of_day desc) AS latest_results WHERE partial=0")
        cursor = self._cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_active_results(self):
        query = ("SELECT game.start_time, game.game_of_day, game.id, course.name, player.name, "
                "sum(result.throws) as res, sum(result.throws - par) as par, count(throws), course.holes "
                "FROM result JOIN hole ON result.hole=hole.id JOIN game ON result.game=game.id "
                    "JOIN player ON player.id=result.player JOIN course ON course.id=game.course "
                "WHERE game.active=true "
                "GROUP BY game.start_time, game.game_of_day, game.id, course.name, course.id, player.name;")
        cursor = self._cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_course_bests(self):
        query = ("SELECT totals.course, totals.player, min(totals.res) as best, "
                "EXTRACT(year FROM totals.start_time) as season FROM ( "
                "SELECT game.course, result.player, game.start_time, game.game_of_day, sum(result.throws) as res, "
                "count(nullif(throws IS NULL, false)) as partial "
                "FROM result JOIN game ON game.id=result.game "
                "WHERE active=false AND special_rules IS NULL "
                "GROUP BY game.course, result.player, game.start_time, game.game_of_day "
                "ORDER BY game.course, result.player, res DESC) as totals "
                "WHERE partial=0 "
                "GROUP BY course, player, season "
                "ORDER BY course, player, season;")
        cursor = self._cursor()
        cursor.execute(query)
        bests = defaultdict(lambda : None)
        for course, player, best, season in cursor.fetchall():
            if not bests[(course, player)] or bests[(course, player)] > best:
                bests[(course, player)] = best
            if not bests[(course, player, season)] or bests[(course, player, season)] > best:
                bests[(course, player, season)] = best
            if not bests[course] or bests[course] > best:
                bests[course] = best
            if not bests[(course, season)] or bests[(course, season)] > best:
                bests[(course, season)] = best

        cursor.close()
        return bests

    def cup_results_2018(self, first_stage=False):
        last_month = 6 if first_stage else 9
        cursor = self._cursor()
        cursor.execute(cup_results_query(2018, 4, last_month))
        results = defaultdict(lambda : (1000, None))
        for player, course, res, date in cursor.fetchall():
            key = (player, course)
            results[key] = (res, date)
        cursor.close()
        return results

    def cup_results_2018_with_handicaps(self, previous_results):
        course_bests = {}
        for player, course in previous_results:
            result, date = previous_results[(player, course)]
            if course in course_bests:
                if course_bests[course] > result:
                    course_bests[course] = result
            else:
                course_bests[course] = result
        cursor = self._cursor()
        cursor.execute(cup_results_query(2018, 7, 9))
        results = defaultdict(lambda : (1000, 1000, 1000, None))
        for player, course, res, date in cursor.fetchall():
            key = (player, course)
            handicap = previous_results[key][0] if key in previous_results else course_bests[course]
            results[key] = (int(res - handicap), int(handicap), int(res), date)
        cursor.close()
        return results

    def cup_results_2017(self):
        sql = ("SELECT cup, player, cup_results.course, game, LEAST(cup_max, summa-pars.par) as res, time "
                "FROM ( "
                    "SELECT course.id as course, sum(par) as par "
                    "FROM hole JOIN course ON hole.course=course.id "
                    "GROUP BY course.id "
                ") as pars JOIN ( "
                    "SELECT DISTINCT ON (cup, player) cup, player, course, game, cup_max, summa, time FROM ( "
                        "SELECT cup.id as cup, player.id as player, course.id as course, game.id as game, "
                               "cup.max_par as cup_max, sum(throws) as summa, game.start_time as time "
                        "FROM course JOIN cup ON cup.course=course.id "
                                    "JOIN game ON game.course=course.id "
                                        "AND EXTRACT(year FROM game.start_time)=cup.year "
                                        "AND EXTRACT(month FROM game.start_time)=cup.month "
                                    "JOIN result ON result.game=game.id "
                                    "JOIN player ON result.player=player.id "
                        "WHERE player.member=true AND game.unfinished=false AND game.active=false "
                        "GROUP BY cup.id, player.id, course.id, game.id, cup.max_par "
                        "ORDER BY course.name, summa "
                    ") as results "
                    "ORDER BY cup, player, summa "
                ") as cup_results ON cup_results.course=pars.course "
                "ORDER BY cup, res")
        cursor = self._cursor()
        cursor.execute(sql)
        results = defaultdict(lambda : (None,None,None,None))
        points = defaultdict(lambda : 0)
        current_cup = None
        counter = 0
        POINTS = (8, 6, 5, 4, 3, 2, 1)
        for cup, player, course, game, cup_result, dt in cursor.fetchall():
            time = dt.strftime("%Y-%m-%d")
            results[(cup, player)] = (course, game, cup_result, time)
            if not current_cup:
                current_cup = cup
            if current_cup != cup:
                current_cup = cup
                counter = 0

            if counter < len(POINTS):
                if points[(cup, cup_result)] == 0:
                    points[(cup, cup_result)] = POINTS[counter]
                    counter += 1

            else:
                points[(cup, cup_result)] = 1
        cursor.close()
        return results, points

    def course_versions(self, course_id):
        cursor = self._cursor()
        sql = "SELECT name FROM course WHERE id=%s"
        cursor.execute(sql, (course_id, ))
        (name, ) = cursor.fetchone()
        sql = "SELECT id FROM course WHERE name=%s ORDER BY version"
        cursor.execute(sql, (name, ))
        versions = []
        for (course_id, ) in cursor.fetchall():
            versions.append(course_id)
        cursor.close()
        return versions

    def player_stats(self, player_id):
        cursor = self._cursor()
        sql = (
            "SELECT course.id, course.name, course.holes, course.version, "
                "par, count, best.start_time::date, throws, throws - par "
            "FROM course "
            "JOIN ("
                "SELECT DISTINCT ON (course) course, throws, start_time "
                "FROM ("
                    "SELECT course, sum(throws) as throws, start_time, "
                        "count(nullif(throws IS NULL, false)) as incomplete "
                    "FROM result "
                    "JOIN game ON game.id=result.game "
                    "WHERE result.player=%s GROUP BY game.id "
                ") AS results "
                "WHERE incomplete=0 "
                "ORDER BY course, throws "
            ") AS best ON course.id=best.course "
            "JOIN (SELECT course, sum(par) as par FROM hole GROUP BY course) "
             "AS pars ON pars.course=course.id "
            "JOIN ( "
                "SELECT course, count(*) FROM ("
                    "SELECT course, game.id, "
                        "count(nullif(throws IS NULL, false)) as incomplete "
                    "FROM game JOIN result ON game.id=result.game "
                    "WHERE result.player=%s GROUP BY course, game.id "
                ") AS games "
                "WHERE incomplete=0 GROUP BY course "
            ") AS game_count ON game_count.course=course.id "
            "ORDER BY course.name, course.version;")
        cursor.execute(sql, (player_id, player_id))
        stats = cursor.fetchall()
        cursor.close()
        return stats


    def graphdata(self, course_id, player_id, averaged):
        cursor = self._cursor()
        sql = "SELECT sum(par) FROM hole WHERE course=%s"
        cursor.execute(sql, (course_id, ))
        (par, ) = cursor.fetchone()
        items = []
        if averaged:
            groups = [
                    {'id': 'min', 'content': 'minimi', 'options': {'shaded': {'orientation': 'group', 'groupId': 'avg'}}},
                    {'id': 'avg', 'content': 'keskiarvo'},
                    {'id': 'max', 'content': 'maximi', 'options': {'shaded': {'orientation': 'group', 'groupId': 'avg'}}},
                    {'id': 'par', 'content': 'par'},
                ]
            sql = ("SELECT max(start_time) as start_time, name, min(res), avg(res), max(res) "
                "FROM ("
                    "SELECT max(game.start_time) as start_time, player.name, sum(result.throws) as res, "
                    "count(nullif(throws IS NULL, false)) as incomplete "
                    "FROM result "
                        "JOIN game ON result.game=game.id "
                        "JOIN player ON player.id=result.player "
                    "WHERE game.course=%s AND game.active=false  AND player=%s "
                    "AND special_rules IS NULL "
                    "GROUP BY game.id, player.name "
                ") AS results WHERE incomplete=0 "
                "GROUP BY EXTRACT(year FROM start_time), EXTRACT(%s FROM start_time), name "
                "ORDER BY start_time, name;")
            cursor.execute(sql, (course_id, player_id, averaged))
            for start_time, name, min_res, avg_res, max_res in cursor.fetchall():
                start_time = int(start_time.strftime('%s'))*1000
                items.append({'x': start_time, 'y': float(min_res)-par, 'group': 'min'})
                items.append({'x': start_time, 'y': float(avg_res)-par, 'group': 'avg'})
                items.append({'x': start_time, 'y': float(max_res)-par, 'group': 'max'})
        else:
            groups = [
                    {'id': 'res', 'content': 'Tulos'},
                    {'id': 'par', 'content': 'par'},
                ]
            sql = ("SELECT start_time, name, throws FROM ("
                    "SELECT game.start_time, player.name, sum(result.throws) as throws, "
                        "count(nullif(throws IS NULL, false)) as incomplete "
                    "FROM result "
                        "JOIN game ON result.game=game.id "
                        "JOIN player ON player.id=result.player "
                    "WHERE game.course=%s AND game.active=false AND special_rules IS NULL AND player=%s "
                    "GROUP BY game.id, player.name) AS foo WHERE incomplete=0 "
                    "ORDER BY start_time, name")
            cursor.execute(sql, (course_id, player_id))
            for start_time, name, res in cursor.fetchall():
                start_time = int(start_time.strftime('%s'))*1000
                items.append({'x': start_time, 'y': res-par, 'group': 'res'})

        min_time, max_time = items[0]['x'], items[-1]['x']
        items.append({'x': min_time, 'y': 0, 'group': 'par'})
        items.append({'x': max_time, 'y': 0, 'group': 'par'})
        cursor.close()

        return {'groups': groups, 'items': items}

    def throw_stats(self, filters):
        inner_rules = []
        values = []
        if 'course' in filters:
            inner_rules.append(" game.course IN %s ")
            values.append(tuple(filters['course']))
        if 'player' in filters:
            inner_rules.append(" result.player IN %s ")
            values.append(tuple(filters['player']))
        if 'begin' in filters and filters['begin'][0]:
            inner_rules.append(" game.start_time >= %s ")
            values.append(filters['begin'][0])
        if 'end' in filters and filters['end'][0]:
            inner_rules.append(" game.start_time <= %s ")
            values.append(filters['end'][0])

        outer_rules = []
        if 'only_complete' in filters:
            outer_rules.append(" incomplete=0 ")

        sql = """
            SELECT count(*) as games, sum(holes) as holes, sum(result) as throws,
                    min(result), avg(result), sum(penalties) as penalties, max(par) as par,
                    course, player
            FROM (
                SELECT count(*) as holes, count(nullif(throws IS NULL, false)) as incomplete,
                    sum(throws) as result, sum(hole.par) as par,
                    sum(penalty) as penalties,
                    game.id as game, player.id as player, game.course
                FROM result
                JOIN hole ON hole.id=result.hole
                JOIN game ON game.id=result.game
                JOIN player ON player.id=result.player
                {inner_where}
                GROUP BY game.id, player.id
            ) AS foo
            {outer_where}
            GROUP BY course, player
            ORDER BY holes DESC;""".format(
                inner_where='WHERE ' + ' AND '.join(inner_rules) if inner_rules else '',
                outer_where='WHERE ' + ' AND '.join(outer_rules) if outer_rules else '')

        cursor = self._cursor()
        cursor.execute(sql, values)
        rows = []
        for games, holes, throws, best, avg, penalties, par, course, player in cursor.fetchall():
            rows.append({
                    'games': int(games), 'holes': int(holes), 'throws': int(throws), 'penalties': int(penalties),
                    'best': int(best), 'avg': float(avg), 'par': int(par), 'course': int(course), 'player': int(player),
                })
        cursor.close()
        return {
                'rows': rows,
                'rules': inner_rules,
            }

    def players_data(self, as_dict=False):
        players = {} if as_dict else []
        cursor = self._cursor()
        sql = "SELECT id, name, member, active, esko_rating FROM player ORDER BY name"
        cursor.execute(sql)
        for player_id, name, member, active, rating in cursor.fetchall():
            player = {'name': name, 'id': player_id, 'member': member, 'active': active,
                      'rating': int(rating*1000) if rating else None}
            if as_dict:
                players[player_id] = player
            else:
                players.append(player)
        cursor.close()
        return {'players': players}

    def courses_data(self, as_dict=False):
        courses = {} if as_dict else []
        course_bests = self.bests_of_courses_data()
        cursor = self._cursor()
        sql = """
            SELECT course.id, name, official_name, holes, version, course.description, town, sum(esko_rating),
                    sum(length) as length, avg(length), max(length), min(length),
                    sum(par) as par, avg(par), max(par), min(par), playable
            FROM course JOIN hole ON hole.course=course.id
            GROUP BY course.id, name, official_name, holes, version, course.description, town
            ORDER BY name, holes, version"""
        cursor.execute(sql)
        for (course_id, name, official_name, holes, version, description, town, rating,
            length, avg_len, longest, shortest, par, avg_par, max_par, min_par, playable) in cursor.fetchall():
            course = {
                    'name': name, 'id': course_id, 'official_name': official_name,
                    'holes': holes, 'version': str(version), 'town': town,
                    'length': length, 'longest': longest, 'shortest': shortest,
                    'par': par, 'avg_par': float(avg_par), 'max_par': max_par, 'min_par': min_par,
                    'playable': playable, 'rating': int(rating*1000) if rating else None,
                    'avg_length': int(avg_len) if avg_len else None,
                    'best': course_bests[course_id] if course_id in course_bests else None,
                }
            if as_dict:
                courses[course_id] = course
            else:
                courses.append(course)
        cursor.close()
        return {'courses': courses}

    def course_data(self, course_id):
        course_bests = self.course_bests_data(course_id)
        cursor = self._cursor()
        sql = """
            SELECT course.id, name, official_name, holes, version, course.description, town, sum(esko_rating),
                    sum(length) as length, avg(length), max(length), min(length),
                    sum(par) as par, avg(par), max(par), min(par), playable
            FROM course JOIN hole ON hole.course=course.id
            WHERE course.id={course_id}
            GROUP BY course.id, name, official_name, holes, version, course.description, town
            ORDER BY name, holes, version""".format(course_id=int(course_id))
        cursor.execute(sql)
        (course_id, name, official_name, holes, version, description, town, rating,
            length, avg_len, longest, shortest, par, avg_par, max_par, min_par, playable) = cursor.fetchone()
        course = {
                'name': name, 'id': course_id, 'official_name': official_name,
                'holes': holes, 'version': str(version), 'town': town,
                'length': length, 'longest': longest, 'shortest': shortest,
                'par': par, 'avg_par': float(avg_par), 'max_par': max_par, 'min_par': min_par,
                'playable': playable, 'bests': course_bests, 'rating': int(rating*1000) if rating else None,
                'avg_length': int(avg_len) if avg_len else None,
                'holes_data': self.holes_data(course_id),
            }
        cursor.close()
        return course

    def holes_data(self, course_id, as_dict=False):
        holes = {} if as_dict else []
        cursor = self._cursor()
        sql = """
            SELECT hole.id, course, hole.hole, description, par,
                length, height, elevation, hole.type, hole_terrain,
                ob_area, mando, gate, island, esko_rating, count(*)
            FROM hole
            LEFT OUTER JOIN hole_map_item ON hole.id=hole_map_item.hole
            WHERE course=%s
            GROUP BY hole.id, course, hole.hole, description, par,
                length, height, elevation, hole.type, hole_terrain,
                ob_area, mando, gate, island, esko_rating
            ORDER BY hole.hole;"""
        cursor.execute(sql, (course_id, ))
        for (hole_id, course, hole, description, par, length, height, elevation, hole_type,
            terrain, ob_area, mando, gate, island, rating, map_item_count) in cursor.fetchall():
            hole = {
                    'id': hole_id, 'course': course, 'hole': hole, 'description': description, 'par': par,
                    'length': length, 'height': height, 'elevation': elevation, 'hole_type': hole_type,
                    'terrain': terrain, 'ob_area': ob_area, 'mando': mando, 'island': island,
                    'rating': int(rating*1000) if rating else None,
                    'map': True if map_item_count > 1 else False,
                }
            if as_dict:
                holes[hole_id] = hole
            else:
                holes.append(hole)
        cursor.close()
        return holes

    def hole_data(self, hole_id):
        cursor = self._cursor()
        sql = """SELECT id, course, hole, description, par,
                    length, height, elevation, type, hole_terrain,
                    ob_area, mando, gate, island, esko_rating
                FROM hole WHERE id=%s ORDER BY hole"""
        cursor.execute(sql, (hole_id, ))
        (hole_id, course, hole, description, par, length, height, elevation, hole_type,
            terrain, ob_area, mando, gate, island, rating) = cursor.fetchone()
        hole = {
                'id': hole_id, 'course': course, 'hole': hole, 'description': description, 'par': par,
                'length': length, 'height': height, 'elevation': elevation, 'hole_type': hole_type,
                'terrain': terrain, 'ob_area': ob_area, 'mando': mando, 'island': island,
                'rating': int(rating*1000) if rating else None,
            }
        cursor.close()
        return hole

    def hole_map_data(self, hole_id):
        items = []
        anchors = []
        cursor = self._cursor()
        sql = "SELECT type, x, y FROM hole_map_item WHERE hole=%s ORDER BY type, id;"
        cursor.execute(sql, (hole_id, ))
        for item_type, x, y in cursor.fetchall():
            if item_type in ('anchor', 'hole'):
                anchors.append({'type': item_type, 'x': x, 'y': y})
            else:
                items.append({'type': item_type, 'x': x, 'y': y})
        cursor.close()
        return {'items': items, 'anchors': anchors}

    def update_map_data(self, hole_id, items):
        cursor = self._cursor()
        delete_query = "DELETE FROM hole_map_item WHERE hole=%s"
        cursor.execute(delete_query, (hole_id, ))
        values = []
        place_holders = []
        for item in items:
            values.append(item['type'])
            values.append(item['x'])
            values.append(item['y'])
            values.append(hole_id)
            place_holders.append('(%s,%s,%s,%s)')
        sql = "INSERT INTO hole_map_item(type, x, y, hole) VALUES {};".format(','.join(place_holders))
        cursor.execute(sql, tuple(values))
        cursor.close()

    def bests_of_courses_data(self):
        sql = """
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
            ORDER BY course, res, start_time;"""
        cursor = self._cursor()
        cursor.execute(sql)
        bests = {}
        for course_id, res, name, player_id, game_date in cursor.fetchall():
            bests[course_id] = {'name': name, 'player_id': player_id, 'result': res, 'date': str(game_date)}
        cursor.close()
        return bests

    def course_bests_data(self, course_id):
        sql = """
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
            ORDER BY rules, season, res, start_time;""".format(course_id=int(course_id))
        cursor = self._cursor()
        cursor.execute(sql)
        bests = {}
        for season, rules, res, name, player_id, game_date in cursor.fetchall():
            season = int(season)
            result = {'name': name, 'player_id': player_id, 'result': res, 'date': str(game_date), 'season': season}
            if rules in bests:
                if bests[rules]['best']['result'] > res:
                    bests[rules]['best'] = result
                bests[rules]['seasons'].append(result)
            else:
                bests[rules] = {'best': result, 'seasons': [result]}
        cursor.close()
        return bests

    def game_data(self, game_id):
        cursor = self._cursor()
        sql = """SELECT active, unfinished, course, start_time, end_time, game_of_day, special_rules
                FROM game WHERE id={game_id}""".format(game_id=int(game_id))
        cursor.execute(sql)
        active, unfinished, course, start_time, end_time, game_of_day, special_rule_id = cursor.fetchone()
        game_data = {
                'active': active, 'unfinished': unfinished, 'course_id': course, 'players': [],
                'start_time': str(start_time), 'end_time': str(end_time), 'game_of_day': game_of_day,
            }
        special_rules = None
        if special_rule_id:
            sql = "SELECT name, description FROM special_rules WHERE id={rules_id}".format(
                    rules_id=int(special_rule_id)
                )
            cursor.execute(sql)
            rule_name, rule_description = cursor.fetchone()
            special_rules = {'id': special_rule_id, 'name': rule_name, 'description': rule_description}
        game_data['special_rules'] = special_rules
        #TODO does not work
        sql = """SELECT player.id, player.name, hole.id, hole.hole,
                        throws, penalty, approaches, puts, reported_at
                FROM result JOIN hole ON hole.id=result.hole
                JOIN player ON player.id=result.player
                WHERE game={game_id} ORDER BY player.name, hole.hole""".format(game_id=int(game_id))
        cursor.execute(sql)
        results = []
        player_results = []
        previous_player = None
        for player_id, name, hole_id, hole, throws, penalty, approaches, puts, reported_at in cursor.fetchall():
            result = {
                    'player_id': player_id, 'name': name, 'hole_id': hole_id, 'hole': hole,
                    'throws': throws, 'penalty': penalty, 'approaches': approaches, 'puts': puts,
                    'reported_at': str(reported_at),
                }
            if not previous_player:
                previous_player = player_id
            if previous_player != player_id:
                results.append(player_results)
                player_results = []
            player_results.append(result)
            previous_player = player_id
        cursor.close()
        game_data['results'] = results
        return game_data

    def new_rule_set(self, name, description):
        sql = "INSERT INTO special_rules(name, description) VALUES (%s,%s) RETURNING id;"
        cursor = self._cursor()
        cursor.execute(sql, (name, description))
        (rule_id, ) = cursor.fetchone()
        return rule_id

    def course_rule_sets(self, course_id):
        rule_sets = []
        sql = ("SELECT game.special_rules, name, description, count(*) "
                "FROM special_rules "
                "RIGHT OUTER JOIN game ON game.special_rules=special_rules.id "
                "WHERE course={course_id} "
                "GROUP BY game.special_rules, name, description "
                "ORDER BY game.special_rules IS NOT NULL, name").format(
                course_id=int(course_id)
            )
        cursor = self._cursor()
        cursor.execute(sql)
        for rule_id, name, description, games in cursor.fetchall():
            if not rule_id:
                rule_sets.append({'id': 0, 'name': 'Standard', 'description': '', 'games': games})
            else:
                rule_sets.append({'id': rule_id, 'name': name, 'description': description, 'games': games})
        return rule_sets

    def course_results_data(self, course_id):
        results = []
        sql = ("SELECT game.id as game_id, game.start_time, game.end_time, game_of_day, game.special_rules, "
                    "player.id as player_id, player.name, player.member, "
                    "result.id as result_id, result.hole as hole_id, throws, penalty, "
                    "approaches, puts, reported_at, hole.hole as hole_num "
                "FROM result "
                "JOIN game ON game.id=result.game "
                "JOIN hole ON hole.id=result.hole "
                "JOIN player ON player.id=result.player "
                "WHERE game.course={course_id} AND NOT game.active "
                "ORDER BY game.start_time DESC, game_of_day DESC, name, hole.hole").format(
                course_id=int(course_id),
            )
        cursor = self._cursor()
        cursor.execute(sql)
        all_results = []
        game = None
        player = None
        previous_game, previous_player, previous_game_of_day = None, None, None
        for (game_id, start_time, end_time, game_of_day, rules, player_id, name, member, result_id, hole_id,
                throws, penalty, approaches, puts, reported_at, hole_num) in cursor.fetchall():
            if previous_game != game_id:
                if game:
                    all_results.append(game)
                game = {'id': game_id, 'start_time': str(start_time)[:10],
                        'end_time': str(end_time)[:10] if end_time else None,
                        'rules': rules, 'game_of_day': game_of_day, 'players': []}
            if previous_player != player_id or previous_game != game_id:
                if player:
                    if previous_game != game_id:
                        all_results[-1]['players'].append(player)
                    else:
                        game['players'].append(player)
                player = {'id': player_id, 'name': name, 'full': True, 'member': member, 'results': []}
            player['full'] = bool(player['full'] and throws)
            player['results'].append({'id': result_id, 'hole': hole_id, 'hole_num': hole_num,
                                        'reported_at': str(reported_at) if reported_at else None,
                                    'throws': throws, 'penalty': penalty, 'approaches': approaches, 'puts': puts})
            previous_game, previous_player, previous_game_of_day = game_id, player_id, game_of_day
        if player:
            game['players'].append(player)
        if game:
            all_results.append(game)
        return {'games': all_results}

    def end_game(self, game_id, unfinished):
        query = "UPDATE player SET active=NULL WHERE active=%s"
        cursor = self._cursor()
        cursor.execute(query, (game_id, ))
        query = ("SELECT now() - start_time, sum(throws) FROM game "
                "JOIN result ON game.id=result.game WHERE game.id=%s "
                "GROUP BY now() - start_time")
        cursor.execute(query, (game_id, ))
        game_time, throws = cursor.fetchone()
        impossible_time = (
                not game_time or game_time < datetime.timedelta(minutes=15) or game_time > datetime.timedelta(hours=4)
            )
        if not throws:
            query = "DELETE FROM game WHERE id=%s"
            cursor.execute(query, (game_id, ))
        else:
            query = "UPDATE game SET active=false, end_time={end_time}, unfinished=%s WHERE id=%s".format(
                    end_time='NULL' if unfinished in (u'true', u'True') or impossible_time else 'now()'
                )
            cursor.execute(query, (unfinished, game_id))
        cursor.close()

    def calculate_esko_ratings(self, use_old_hole_ratings=False):
        sql = "SELECT course, hole, esko_rating FROM hole ORDER BY course, hole;"
        hole_ratings = {}
        played = {}
        if use_old_hole_ratings:
            cursor = self._cursor()
            cursor.execute(sql)
            for course, hole, rating in cursor.fetchall():
                if course not in hole_ratings:
                    hole_ratings[course] = defaultdict(lambda: 0)
                    played[course] = defaultdict(lambda: 0)
                hole_ratings[course][hole] = rating if rating else 0
            cursor.close()

        player_data = self.players_data(as_dict=True)['players']
        courses_data = self.courses_data(as_dict=True)['courses']
        query = ("SELECT EXTRACT('month' FROM game.start_time), game.course, player.id, hole.hole, throws - hole.par "
                "FROM result "
                "JOIN game ON result.game=game.id "
                "JOIN hole ON result.hole=hole.id "
                "JOIN player ON result.player=player.id "
                "WHERE special_rules IS NULL AND throws IS NOT NULL AND player.member "
                "ORDER BY game.start_time, hole.hole;")
        cursor = self._cursor()
        cursor.execute(query)
        evidence = defaultdict(lambda: 0)
        players = defaultdict(lambda: 0)
        previous_year = None

        for year, course, player, hole, result in cursor.fetchall():
            if not use_old_hole_ratings and course not in hole_ratings:
                hole_ratings[course] = defaultdict(lambda: 0)
                played[course] = defaultdict(lambda: 0)
            if not previous_year:
                previous_year = year

            # if year != previous_year:
            #     print '-- month-- ', int(year)
            #     pratings = []
            #     for player in players:
            #         pratings.append((players[player], player_data[player]['name']))
            #     pratings.sort()
            #     for r in pratings:
            #         print r[1], r[0]
            #     previous_year = year

            diff = result - (hole_ratings[course][hole] + players[player])
            if result < 5:
                if played[course][hole] >= 10:
                    if evidence[player] < 50:
                        players[player] += 0.1*diff
                    else:
                        players[player] += 0.01*diff
                if evidence[player] >= 50:
                    if played[course][hole] < 10:
                        hole_ratings[course][hole] += 0.3*diff
                    else:
                        hole_ratings[course][hole] += 0.02*diff

            # if player == 19 and year != previous_year:
            #     print year, players[player]
            #     previous_year = year

            # if course == 38 and year != previous_year:
            #     print int(year), sum([hole_ratings[course][hole] for hole in hole_ratings[course]])
            #     previous_year = year

            played[course][hole] += 1.0
            evidence[player] += 1.0
            #previous_year = year

        cursor.close()

        print('---- final ----')
        pratings = []
        for player in players:
            pratings.append((players[player], player_data[player]['name']))
        pratings.sort()
        for r in pratings:
            print(r[1], r[0])

        # rated_courses = []
        # for course in hole_ratings:
        #     data = (sum([hole_ratings[course][hole] for hole in hole_ratings[course]]),
        #             courses_data[course]['name'],
        #             courses_data[course]['holes'])
        #     rated_courses.append(data)
        # rated_courses.sort()
        # for course in rated_courses:
        #     print course

        # print "Puolari"
        # for hole in hole_ratings[38]:
        #     print hole,  hole_ratings[38][hole]

        # print "Nummela"
        # for hole in hole_ratings[1]:
        #     print hole,  hole_ratings[1][hole]

        player_update = "UPDATE player SET esko_rating=%s WHERE id=%s"
        course_update = "UPDATE hole SET esko_rating=%s WHERE course=%s AND hole=%s"
        cursor = self._cursor()
        for player in players:
            cursor.execute(player_update, (players[player], player))
        for course in hole_ratings:
            for hole in hole_ratings[course]:
                if played[course][hole] >= 3:
                    cursor.execute(course_update, (hole_ratings[course][hole], course, hole))
                else:
                    cursor.execute(course_update, (None, course, hole))
        cursor.close()




if __name__ == '__main__':
    pass
