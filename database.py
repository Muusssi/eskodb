import psycopg2
import datetime
from collections import defaultdict

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

    def game_times(self, course_id):
        sql = ("SELECT min(end_time-start_time), avg(end_time-start_time), max(end_time-start_time), pools.size "
                "FROM game JOIN (SELECT count(*) as size, game FROM result JOIN hole ON hole.id=result.hole "
                "WHERE hole.hole=1 AND hole.course=%s GROUP BY game) AS pools ON pools.game=game.id "
                "WHERE game.course=%s GROUP BY pools.size ORDER BY pools.size")
        cursor = self._cursor()
        cursor.execute(sql, (course_id, course_id))
        times = []
        for min_time, avg_time, max_time, pool_size in cursor.fetchall():
            if min_time:
                min_time = ':'.join(str(min_time).split('.')[0].split(':')[:2])
                avg_time = ':'.join(str(avg_time).split('.')[0].split(':')[:2])
                max_time = ':'.join(str(max_time).split('.')[0].split(':')[:2])
                times.append((min_time, avg_time, max_time, pool_size))
        cursor.close()
        if not times:
            times.append(("###", "###", "###", 0))
        return times

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


    # def get_hole_statistics(self, course, hole):
    #     query = ("SELECT throws, player, game_date, game_of_day "
    #             "FROM results "
    #             "WHERE course=%s AND hole=%s AND player<>'par' "
    #             "AND player not like 'Target%s'") % (course, hole, '%')
    #     cursor = self._cursor()
    #     cursor.execute(query)
    #     results = []
    #     for throws, player, game_date, game_of_day in cursor.fetchall():
    #         results.append(["%s: %s #%s" % (player, game_date, game_of_day), throws])
    #     cursor.close()
    #     return {'rows': results}


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
        if 'begin' in filters:
            inner_rules.append(" game.start_time >= %s ")
            values.append(filters['begin'][0])
        if 'end' in filters:
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
            #print games, holes, throws, best, avg, penalties, par, course, player
            rows.append({
                    'games': int(games), 'holes': int(holes), 'throws': int(throws), 'penalties': int(penalties),
                    'best': int(best), 'avg': float(avg), 'par': int(par), 'course': int(course), 'player': int(player),
                })
        cursor.close()
        return {
                'rows': rows,
                'rules': inner_rules,
            }

    # def get_probabilities(self, course_id, player):
    #     cursor = self._cursor()
    #     query = ("SELECT hole, throws, CAST (count(*) AS FLOAT)/( "
    #             "SELECT count(*) FROM ( "
    #             "SELECT DISTINCT game_date, game_of_day "
    #             "FROM results "
    #             "WHERE course=%s AND player=%s) as games) "
    #             "FROM results "
    #             "WHERE course=%s AND player=%s "
    #             "GROUP BY hole, throws "
    #             "ORDER BY hole, throws")
    #     cursor.execute(query, (course_id, player, course_id, player))
    #     max_throws = 1
    #     prev_level = dict()
    #     new_level = {0: 1}
    #     current_hole = 0
    #     for hole, throws, prob in cursor.fetchall():
    #         if throws > max_throws:
    #             max_throws = throws
    #         if current_hole != hole:
    #             current_hole = hole
    #             prev_level = new_level
    #             new_level = dict()

    #         for res in prev_level:
    #             new_res = res+throws
    #             if new_res in new_level:
    #                 new_level[new_res] += prev_level[res]*prob
    #             else:
    #                 new_level[new_res] = prev_level[res]*prob
    #     cursor.close()
    #     probs = []
    #     for x in sorted(new_level.keys()):
    #         probs.append((x, new_level[x]))
    #     return probs


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


if __name__ == '__main__':
    pass

