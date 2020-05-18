import psycopg2
import datetime
from collections import defaultdict
import json
import sys

import sql_queries

GAME_TEMPLATE = "%s #%s"

CUP_DATES = {
    2019: ('2019-04-15', '2019-07-15', '2019-10-15'),
    2020: ('2020-05-12', '2020-08-02', '2020-10-18'),
}

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

    def fetch_rows(self, table, fields, criteria={}, order_by="", join_rule="", additional_where=""):
        criteria_fields, values = _fields_and_values(criteria)
        sql = "SELECT %s FROM %s" % (','.join(['{}.{}'.format(table, field) for field in fields]), table)
        if join_rule:
            sql += join_rule
        if criteria or additional_where:
            sql += " WHERE "
            if criteria:
                sql += ' AND '.join(['{}=%s'.format(field) for field in criteria_fields])
            if additional_where:
                if criteria:
                    sql += ' AND '
                sql += additional_where
        if order_by:
            sql += " ORDER BY %s" % order_by
        cursor = self._cursor()
        cursor.execute(sql, values)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def update_row(self, table, values, row_id):
        fields, values = _fields_and_values(values)
        sql = "UPDATE {} SET {} WHERE id={} ".format(table, ','.join(['{}=%s'.format(field) for field in fields]), int(row_id))
        cursor = self._cursor()
        cursor.execute(sql, values)
        cursor.close()


    def insert_row(self, table, values):
        fields, values = _fields_and_values(values)
        sql = "INSERT INTO {}({}) VALUES ({}) RETURNING id".format(
                table, ','.join(fields), ','.join(['%s' for _ in values])
            )
        cursor = self._cursor()
        cursor.execute(sql, values)
        (row_id, ) = cursor.fetchone()
        cursor.close()
        return row_id

    def generate_empty_results(self, game, player_ids):
        cursor = self._cursor()
        cursor.execute(sql_queries.holes_of_course(game.course))
        hole_ids = []
        for (hole_id, ) in cursor.fetchall():
            hole_ids.append(hole_id)

        sql = "INSERT INTO result(game, player, hole, reported_at) VALUES {}"
        values = []
        for player_id in player_ids:
            for hole_id in hole_ids:
                values.append("({},{},{},null)".format(game.id, player_id, hole_id))
        sql = sql.format(','.join(values))
        cursor.execute(sql)
        cursor.close()

    def previous_hole_stats(self, game_id):
        cursor = self._cursor()
        cursor.execute("SELECT special_rules FROM game WHERE id={}".format(int(game_id)))
        (special_rules, ) = cursor.fetchone()
        cursor.execute(sql_queries.previous_hole_stats(game_id, special_rules))
        results = {}
        for player, hole, hole_id, avg, minimum, count in cursor.fetchall():
            avg = float(avg) if avg else None
            if player not in results:
                results[player] = {}
            results[player][hole_id] = {'hole': hole, 'avg': avg, 'min': minimum, 'count': count}
        cursor.close()
        return results

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
        cursor = self._cursor()
        cursor.execute(sql_queries.game_times(course_id))
        game_times = []
        previous_rules = None
        for size, rules, games, min_time, avg_time, max_time, name in cursor.fetchall():
            if not previous_rules or previous_rules['id'] != rules:
                if previous_rules:
                    game_times.append(previous_rules)
                previous_rules = {'id': rules, 'name': name, 'times': []}

            previous_rules['times'].append({
                    'pool': size, 'games': games, 'min': datetime_to_hour_minutes(min_time),
                    'avg': datetime_to_hour_minutes(avg_time), 'max': datetime_to_hour_minutes(max_time),
                })
        if previous_rules:
            game_times.append(previous_rules)
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
        cursor = self._cursor()
        cursor.execute(sql_queries.LATEST_GAMES)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_active_results(self):
        cursor = self._cursor()
        cursor.execute(sql_queries.ACTIVE_RESULTS)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_course_bests(self):
        cursor = self._cursor()
        cursor.execute(sql_queries.COURSE_BESTS)
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

    def cup_results_2019_rules(self, year, stage=None):
        cursor = self._cursor()
        if stage == 1:
            cursor.execute(sql_queries.cup_results_query(year, CUP_DATES[year][0], CUP_DATES[year][1]))
        elif stage == 2:
            cursor.execute(sql_queries.cup_results_query(year, CUP_DATES[year][1], CUP_DATES[year][2]))
        else:
            cursor.execute(sql_queries.cup_results_query(year, CUP_DATES[year][0], CUP_DATES[year][2]))
        results = defaultdict(lambda : (1000, None))
        course_bests = defaultdict(lambda : None)
        point_dict = defaultdict(lambda : 0.0)
        previous_course, previous_result = None, None
        points_to_share = []
        tiees = []
        available_points = [20, 17, 15, 13, 12, 11, 10, 9, 8, 7, 6]
        for player, course, res, date in cursor.fetchall():
            key = (player, course)
            results[key] = (res, date)
            if not course_bests[course] or course_bests[course] > res:
                course_bests[course] = res
            # cup points
            if previous_course != course:
                available_points = [20, 17, 15, 13, 12, 11, 10, 9, 8, 7, 6]
            points = available_points.pop(0) if len(available_points) > 0 else 5
            if previous_result != res or previous_course != course:
                for tiee in tiees:
                    point_dict[tiee] = sum(points_to_share)/float(len(tiees))
                points_to_share = []
                tiees = []
            tiees.append(key)
            points_to_share.append(points)
            previous_course, previous_result = course, res
        if tiees:
            for tiee in tiees:
                point_dict[tiee] = sum(points_to_share)/float(len(tiees))
        cursor.close()
        return results, point_dict, course_bests

    def cup_results_2018(self, first_stage=False):
        last_month = '2018-07-01' if first_stage else '2018-10-01'
        cursor = self._cursor()
        cursor.execute(sql_queries.cup_results_query(2018, '2018-04-01', last_month))
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
        cursor.execute(sql_queries.cup_results_query(2018, '2018-07-01', '2018-10-01'))
        results = defaultdict(lambda : (1000, 1000, 1000, None))
        for player, course, res, date in cursor.fetchall():
            key = (player, course)
            handicap = previous_results[key][0] if key in previous_results else course_bests[course]
            results[key] = (int(res - handicap), int(handicap), int(res), date)
        cursor.close()
        return results

    def cup_results_2017(self):
        cursor = self._cursor()
        cursor.execute(sql_queries.CUP_RESULTS_2017)
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
        cursor.execute(sql_queries.player_stats(player_id))
        stats = cursor.fetchall()
        cursor.close()
        return stats


    def graphdata(self, course_id, player_id, averaged):
        cursor = self._cursor()
        sql = "SELECT sum(par) FROM hole JOIN hole_mapping ON hole.id=hole_mapping.hole WHERE course=%s"
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
        cursor.execute(sql_queries.COURSES_DATA)
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
        cursor.execute(sql_queries.course_data(course_id))
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
        cursor.execute(sql_queries.course_images_info(course_id))
        images = []
        for image_id, desc, timestamp in cursor.fetchall():
            images.append({'id': image_id, 'description': desc, 'timestamp': str(timestamp)})
        course['images'] = images
        cursor.close()
        return course

    def generate_default_holes(self, course_id, holes):
        cursor = self._cursor()
        hole_sql = "INSERT INTO hole(length, height) VALUES (NULL, NULL) RETURNING id"
        mapping_sql = "INSERT INTO hole_mapping(course, hole, hole_number) VALUES ({},{},{})"
        for hole_number in range(1, holes + 1):
            cursor.execute(hole_sql)
            (hole_id, ) = cursor.fetchone()
            cursor.execute(mapping_sql.format(int(course_id), hole_id, hole_number))
        cursor.close()

    def merge_holes(self, course1, hole1, course2, hole2):
        cursor = self._cursor()
        cursor.execute(sql_queries.merge_hole_results(course1, hole1, course2, hole2))
        cursor.execute(sql_queries.merge_holes(course1, hole1, course2, hole2))
        cursor.close()

    def change_course(self, game_id, old_course, new_course, holes):
        cursor = self._cursor()
        sql = "UPDATE game set course={new_course} WHERE id={game_id}".format(new_course=int(new_course),
                                                                              game_id=int(game_id))
        cursor.execute(sql)
        for hole_index in range(holes):
            cursor.execute(sql_queries.move_results(game_id, old_course, new_course, hole_index + 1))
        cursor.close()

    def holes_data(self, course_id, as_dict=False):
        cursor = self._cursor()
        cursor.execute(sql_queries.hole_image_data_for_course(course_id))
        images = defaultdict(lambda: [])
        for image_id, hole, hole_number, desc, timestamp in cursor.fetchall():
            images[hole].append({'id': image_id, 'description': desc, 'timestamp': str(timestamp)})

        holes = {} if as_dict else []
        cursor.execute(sql_queries.holes_data(course_id))
        for (hole_id, course, hole, description, par, length, height, elevation, hole_type,
            terrain, ob_area, mando, gate, island, rating, map_item_count) in cursor.fetchall():
            hole = {
                    'id': hole_id, 'course': course, 'hole': hole, 'description': description, 'par': par,
                    'length': length, 'height': height, 'elevation': elevation, 'hole_type': hole_type,
                    'terrain': terrain, 'ob_area': ob_area, 'mando': mando, 'island': island, 'gate': gate,
                    'rating': int(rating*1000) if rating else None,
                    'map': True if map_item_count > 1 else False,
                    'images': images[hole_id],
                }
            if as_dict:
                holes[hole_id] = hole
            else:
                holes.append(hole)
        cursor.close()
        return holes

    def hole_data(self, hole_id):
        cursor = self._cursor()
        cursor.execute(sql_queries.hole_data(hole_id))
        hole = None
        for (hole_id, description, par, length, height, elevation, hole_type,
             terrain, ob_area, mando, gate, island, rating,
             course_id, hole_number, course_name, course_holes, course_version) in cursor.fetchall():
            if not hole:
                hole = {'id': hole_id, 'description': description, 'par': par,
                        'length': length, 'height': height, 'elevation': elevation, 'hole_type': hole_type,
                        'terrain': terrain, 'ob_area': ob_area, 'mando': mando, 'island': island, 'gate': gate,
                        'rating': int(rating*1000) if rating else None, 'included_in_courses': []}
            course = {'id': course_id, 'hole_number': hole_number, 'name': course_name, 'holes': course_holes,
                      'version': str(course_version)}
            hole['included_in_courses'].append(course)
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
        cursor = self._cursor()
        cursor.execute(sql_queries.BESTS_OF_COURSES)
        bests = {}
        for course_id, res, name, player_id, game_date in cursor.fetchall():
            bests[course_id] = {'name': name, 'player_id': player_id, 'result': res, 'date': str(game_date)}
        cursor.close()
        return bests

    def course_bests_data(self, course_id):
        cursor = self._cursor()
        cursor.execute(sql_queries.course_bests(course_id))
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

    def game_results(self, game_id):
        cursor = self._cursor()
        cursor.execute(sql_queries.game_results(game_id))
        players = []
        results = []
        player = None
        previous_player = None
        for (result_id, player_id, name, hole_id, hole,
             throws, penalty, approaches, puts, reported_at) in cursor.fetchall():
            if previous_player != player_id:
                if player:
                    players.append(player)
                player = {'player_id': player_id, 'name': name, 'results': []}
            result = {'id': result_id, 'hole_id': hole_id, 'hole': hole,
                      'throws': throws, 'penalty': penalty, 'approaches': approaches, 'puts': puts,
                      'reported_at': str(reported_at) if reported_at else None}
            player['results'].append(result)
            previous_player = player_id
        if player:
            players.append(player)
        cursor.close()
        return players

    def update_game_results(self, result_ids, player_ids, throws, penalties, approaches, puts):
        cursor = self._cursor()
        for i in range(len(result_ids)):
            values = (
                    throws[i] if throws[i] else None,
                    penalties[i] if penalties[i] else None,
                    approaches[i] if approaches[i] else None,
                    puts[i] if puts[i] else None,
                    result_ids[i] if result_ids[i] else None,
                )
            cursor.execute(sql_queries.UPDATE_RESULT, values)
        cursor.close()

    def game_data(self, game_id):
        cursor = self._cursor()
        sql = """SELECT active, unfinished, course, start_time, end_time, game_of_day, special_rules
                FROM game WHERE id={game_id}""".format(game_id=int(game_id))
        cursor.execute(sql)
        active, unfinished, course, start_time, end_time, game_of_day, special_rule_id = cursor.fetchone()
        game_data = {'id': game_id, 'active': active, 'unfinished': unfinished, 'course_id': course,
                     'start_time': str(start_time), 'end_time': str(end_time), 'game_of_day': game_of_day}
        special_rules = None
        if special_rule_id:
            sql = "SELECT name, description FROM special_rules WHERE id={rules_id}".format(
                    rules_id=int(special_rule_id)
                )
            cursor.execute(sql)
            rule_name, rule_description = cursor.fetchone()
            special_rules = {'id': special_rule_id, 'name': rule_name, 'description': rule_description}
        game_data['special_rules'] = special_rules
        cursor.close()
        game_data['players'] = self.game_results(game_id)
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
        cursor = self._cursor()
        cursor.execute(sql_queries.course_results(course_id))
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
                not game_time or game_time < datetime.timedelta(minutes=15) or game_time > datetime.timedelta(hours=6)
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

    def set_game_time(self, game_id, game_time):
        sql = "UPDATE game SET end_time=(start_time + %s) WHERE id=%s"
        cursor = self._cursor()
        cursor.execute(sql, (game_time, game_id))
        cursor.close()

    def calculate_esko_ratings(self, use_old_hole_ratings=False):
        print("EsKo rating calculator not implemented!")
        exit()
        # TODO: use hole mapping
        sql = "SELECT course, hole, esko_rating FROM hole JOIN  ORDER BY course, hole;"
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

    def store_hole_image(self, hole_id, description, image, extension):
        sql = "INSERT INTO hole_image(hole, description, image, file_type) VALUES (%s,%s,%s,%s);"
        cursor = self._cursor()
        cursor.execute(sql, (hole_id, description, psycopg2.Binary(image), extension))
        cursor.close()

    def store_course_image(self, course_id, description, image, extension):
        sql = "INSERT INTO course_image(course, description, image, file_type) VALUES (%s,%s,%s,%s);"
        cursor = self._cursor()
        cursor.execute(sql, (course_id, description, psycopg2.Binary(image), extension))
        cursor.close()

    def get_hole_image(self, image_id):
        sql = "SELECT image, file_type FROM hole_image WHERE id={}".format(int(image_id))
        cursor = self._cursor()
        cursor.execute(sql)
        image, file_type = cursor.fetchone()
        cursor.close()
        return image, file_type

    def get_course_image(self, image_id):
        sql = "SELECT image, file_type FROM course_image WHERE id={}".format(int(image_id))
        cursor = self._cursor()
        cursor.execute(sql)
        image, file_type = cursor.fetchone()
        cursor.close()
        return image, file_type

def _fields_and_values(criteria):
    fields = []
    values = []
    for field in criteria:
        fields.append(field)
        values.append(criteria[field])
    return fields, values

def load_config_file(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    config = load_config_file(sys.argv[1])
    db = Database(config['database'], config['host'], config['user'], config['password'])
    db.generate_default_holes(85, 18)
    #db.calculate_esko_ratings()