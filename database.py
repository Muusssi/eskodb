import psycopg2
import datetime
from collections import defaultdict

GAME_TEMPLATE = "%s #%s"

class Database(object):

    def __init__(self, pw):
        self.pw = pw
        self._connect()

    def _connect(self):
        self._conn = psycopg2.connect(
                "dbname='eskodb2' user='esko' host='localhost' password='%s'" %
                (self.pw, )
            )

    def _cursor(self):
        return self._conn.cursor()

    def _close_connection(self):
        self._conn.close()

    def _commit(self):
        self._conn.commit()

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
            next_game_of_day = int(res[0])+1
        else:
            next_game_of_day = 1
        cursor.close()
        return next_game_of_day

    def activate_players(self, player_ids, game_id):
        sql = "UPDATE player SET active=%s WHERE id IN %s"
        cursor = self._cursor()
        cursor.execute(sql, (game_id, tuple(player_ids)))
        self._commit()
        cursor.close()

    def next_hole(self, game_id):
        sql = "SELECT max(hole) FROM result WHERE game=%s"
        cursor = self._cursor()
        cursor.execute(sql, (game_id, ))
        res = cursor.fetchone()
        if res:
            hole = 1
        else:
            hole = int(res[0])+1
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
        self._commit()
        cursor.close()


    def insert_row(self, table, values):
        sql = "INSERT INTO %s(%s) VALUES (%s) RETURNING id" % (table, ','.join([col for col in values]), ','.join(['%s' for col in values]))
        cursor = self._cursor()
        cursor.execute(sql, values.values())
        (row_id, ) = cursor.fetchone()
        self._commit()
        cursor.close()
        return row_id

    def generate_empty_results(self, game, player_ids):
        cursor = self._cursor()
        sql = "SELECT id FROM hole WHERE course=%s ORDER BY hole"
        cursor.execute(sql, (game.course, ))
        hole_ids = []
        for (hole_id, ) in cursor.fetchall():
            hole_ids.append(hole_id)

        sql = "INSERT INTO result(game, player, hole) VALUES %s"
        values = []
        for player_id in player_ids:
            for hole_id in hole_ids:
                values.append("(%s,'%s',%s)" % (game.id, player_id, hole_id))
        sql = sql % ','.join(values)
        cursor.execute(sql)
        self._commit()
        cursor.close()

    def game_results(self, game_id):
        cursor = self._cursor()
        sql = "SELECT count(*) FROM player WHERE active=%s"
        cursor.execute(sql, (game_id, ))
        (players, ) = cursor.fetchone()

        sql = ("SELECT result.id, result.player, result.throws, result.penalty, result.drives, result.puts "
                "FROM result JOIN hole on hole.id=result.hole JOIN player ON player.id=result.player "
                "WHERE result.game=%s ORDER BY player.name, hole.hole")
        cursor.execute(sql, (game_id, ))
        result_table = []
        row = []
        current_player = None
        for result_id, player, throws, penalty, drives, puts in cursor.fetchall():
            if not current_player:
                current_player = player
            if current_player != player:
                result_table.append(row)
                row = []
                current_player = player
            row.append([throws, penalty, drives, puts, result_id])
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


    # def get_results2(self, course_id):
    #     cursor = self._cursor()
    #     results = {}
    #     #Fetch course info
    #     query = ("SELECT name, holes FROM courses "
    #              "WHERE id=%s LIMIT 1")
    #     cursor.execute(query, (course_id, ))
    #     course_name, holes = cursor.fetchone()

    #     # Fetch par
    #     query = ("SELECT hole, throws FROM results "
    #              "WHERE course=%s AND player='par' ORDER BY hole ASC")
    #     cursor.execute(query, (course_id, ))
    #     par_row = []
    #     par_sum = 0
    #     for h, t in cursor.fetchall():
    #         par_row.append(t)
    #         par_sum += t
    #     pars = (par_row, par_sum)

    #     # Other results
    #     res_rows = []
    #     index = -1

    #     query = ("SELECT player, hole, throws, penalty, game_date, game_of_day "
    #              "FROM results WHERE course=%s AND player<>'par' "
    #              "ORDER BY game_date, game_of_day, player, hole ASC")
    #     cursor.execute(query, (course_id, ))

    #     current_game = None
    #     current_player = None
    #     row_sum = 0
    #     row = []
    #     for p, h, t, b, d, n in cursor.fetchall():
    #         game = GAME_TEMPLATE % (d, n)
    #         if current_game != game or p != current_player:
    #             if current_game:
    #                 res_rows.append((current_game, current_player, row, row_sum, row_sum-par_sum))
    #             row_sum = 0
    #             row = []
    #             current_game = game
    #             current_player = p
    #         if par_row:
    #             row.append((t, b, t-par_row[h-1]))
    #         else:
    #             row.append((t, b, t-3))
    #         row_sum += t
    #     res_rows.append((current_game, current_player, row, row_sum, row_sum-par_sum))
    #     cursor.close()
    #     return pars, reversed(res_rows)


    def get_latest_games(self):
        query = ("SELECT game.start_time, game.game_of_day, course.name, course.id, "
                "player.name, player.id, sum(result.throws) as res, sum(result.throws) - pars.sum as par "
                "FROM result JOIN game ON result.game=game.id JOIN player ON player.id=result.player "
                "JOIN course ON game.course=course.id JOIN ( "
                    "SELECT course.id as course, sum(par) as sum "
                    "FROM hole JOIN course ON hole.course=course.id "
                    "GROUP BY course.id "
                ") as pars ON pars.course=course.id "
                "WHERE game.start_time > (date 'today' -14) AND game.active=false "
                "GROUP BY game.start_time, game.game_of_day, course.name, course.id, player.name, player.id, pars.sum "
                "ORDER BY game.start_time desc, game.game_of_day desc;")
        cursor = self._cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_course_bests(self):
        query = ("SELECT totals.course, totals.player, min(totals.res) as best, "
                "EXTRACT(year FROM totals.start_time) as season FROM ( "
                "SELECT game.course, result.player, game.start_time, game.game_of_day, sum(result.throws) as res "
                "FROM result JOIN game ON game.id=result.game "
                "GROUP BY game.course, result.player, game.start_time, game.game_of_day "
                "ORDER BY game.course, result.player, res DESC "
                ") as totals "
                "GROUP BY course, player, season "
                "ORDER BY course, player;")
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


    def end_game(self, game_id):
        query = ("UPDATE player SET active=NULL WHERE active=%s")
        cursor = self._cursor()
        cursor.execute(query, (game_id, ))
        query = ("UPDATE game SET active=false, end_time='now' WHERE id=%s")
        cursor = self._cursor()
        cursor.execute(query, (game_id, ))
        self._commit()
        cursor.close()


if __name__ == '__main__':
    DB = Database("kopsupullo")
    print DB.game_results(293)
    DB._close_connection()

