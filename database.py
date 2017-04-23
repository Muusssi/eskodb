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
                "dbname='eskodb' user='esko' host='localhost' password='%s'" %
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

    def get_players(self, course_id=None):
        cursor = self._cursor()
        if course_id:
            query = ("SELECT name FROM players WHERE active=%s ORDER BY name")
            cursor.execute(query, (course_id, ))
        else:
            query = ("SELECT name FROM players ORDER BY name")
            cursor.execute(query)

        res = cursor.fetchall()
        cursor.close()
        return res

    def activate_players(self, players, course_id):
        query = ("UPDATE players SET active=%s WHERE name IN %s")
        cursor = self._cursor()
        cursor.execute(query, (course_id, tuple(players)))
        self._commit()
        cursor.close()

    def get_current_courses(self):
        query = ("SELECT name, holes, max(id) FROM courses GROUP BY name, holes ORDER BY name, holes;")
        cursor = self._cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        cursor.close()
        return res

    def get_courses(self, in_play=False):
        if in_play:
            query = ("SELECT name, holes, id FROM courses WHERE id IN "
                     "(SELECT DISTINCT active FROM players) "
                     "ORDER BY name, holes")
        else:
            query = ("SELECT name, holes, id FROM courses ORDER BY name, holes")
        cursor = self._cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        cursor.close()
        return res

    def get_course(self, course_id):
        query = ("SELECT name, holes, id FROM courses WHERE id=%s")
        cursor = self._cursor()
        cursor.execute(query, (course_id, ))
        res = cursor.fetchone()
        cursor.close()
        return res

    def get_par(self, course_id):
        query = ("SELECT sum(throws) FROM results WHERE course=%s AND player='par'")
        cursor = self._cursor()
        cursor.execute(query, (course_id, ))
        (res, ) = cursor.fetchone()
        cursor.close()
        return res

    def add_course(self, name, holes):
        query = ("SELECT version FROM courses WHERE name=%s AND holes=%s")
        cursor = self._cursor()
        cursor.execute(query, (name, holes))
        if cursor.fetchall():
            cursor.close()
            return False
        else:
            query = ("INSERT INTO courses(name, holes) VALUES (%s, %s);")
            cursor.execute(query, (name, holes))
            self._commit()
            cursor.close()
            return True

    def add_player(self, name):
        query = ("SELECT name FROM players WHERE name=%s")
        cursor = self._cursor()
        cursor.execute(query, (name, ))
        if cursor.fetchall():
            cursor.close()
            return False
        else:
            query = ("INSERT INTO players(name) VALUES (%s);")
            cursor.execute(query, (name, ))
            self._commit()
            cursor.close()
            return True

    def get_hole_statistics(self, course, hole):
        query = ("SELECT throws, player, game_date, game_of_day "
                "FROM results "
                "WHERE course=%s AND hole=%s AND player<>'par' "
                "AND player not like 'Target%s'") % (course, hole, '%')
        cursor = self._cursor()
        cursor.execute(query)
        results = []
        for throws, player, game_date, game_of_day in cursor.fetchall():
            results.append(["%s: %s #%s" % (player, game_date, game_of_day), throws])
        cursor.close()
        return {'rows': results}


    def get_results(self, course_id, in_play=False):
        cursor = self._cursor()
        results = {}
        #Fetch course info
        query = ("SELECT name, holes FROM courses "
                 "WHERE id=%s LIMIT 1")
        cursor.execute(query, (course_id, ))
        course_name, holes = cursor.fetchone()
        results['course'] = {}
        results['course']['course_name'] = course_name
        results['course']['holes'] = holes

        # Fetch par
        query = ("SELECT hole, throws FROM results "
                 "WHERE course=%s AND player='par' ORDER BY hole ASC")
        cursor.execute(query, (course_id, ))
        par_row = [None for k in range(holes+1)]
        par_sum = 0
        for h, t in cursor.fetchall():
            par_row[h] = t
            par_sum += t
        par_row[0] = 'par'
        par_row.append(par_sum)
        if not in_play:
            par_row.insert(0, '')
        results['rows'] = [par_row]

        # Other results
        res_rows = []
        index = -1
        if in_play:
            query = ("SELECT player, hole, throws, penalty "
                     "FROM results WHERE course=%s AND player<>'par' "
                     "AND in_play=true "
                     "ORDER BY player, hole ASC")
            cursor.execute(query, (course_id, ))
            for p, h, t, b in cursor.fetchall():
                if index<0 or p != res_rows[index][0]:
                    index += 1
                    res_rows.append([None for k in range(holes+2)])
                    res_rows[index][0] = p
                    res_rows[index][holes+1] = 0
                if b>0:
                    penalty = ''
                    for k in range(b):
                        penalty += '*'
                    res_rows[index][h] = {'v':t, 'f':str(t)+penalty }
                else:
                    res_rows[index][h] = t
                res_rows[index][holes+1] += t

        else:
            query = ("SELECT player, hole, throws, penalty, game_date, game_of_day "
                     "FROM results WHERE course=%s AND player<>'par' "
                     "ORDER BY game_date, game_of_day, player, hole ASC")
            cursor.execute(query, (course_id, ))

            for p, h, t, b, d, n in cursor.fetchall():
                #print res_rows
                game = GAME_TEMPLATE % (d, n)
                if index<0 or p != res_rows[index][1] or game != res_rows[index][0]:
                    index += 1
                    res_rows.append([None for k in range(holes+3)])
                    res_rows[index][0] = game
                    res_rows[index][1] = p
                    res_rows[index][holes+2] = 0
                if b > 0:
                    penalty = ''
                    for k in range(b):
                        penalty += '*'
                    res_rows[index][1+h] = {'v':t, 'f':str(t)+penalty}
                else:
                    res_rows[index][1+h] = t
                res_rows[index][holes+2] += t

        results['rows'].extend(reversed(res_rows))

        cursor.close()
        return results

    def get_results2(self, course_id):
        cursor = self._cursor()
        results = {}
        #Fetch course info
        query = ("SELECT name, holes FROM courses "
                 "WHERE id=%s LIMIT 1")
        cursor.execute(query, (course_id, ))
        course_name, holes = cursor.fetchone()

        # Fetch par
        query = ("SELECT hole, throws FROM results "
                 "WHERE course=%s AND player='par' ORDER BY hole ASC")
        cursor.execute(query, (course_id, ))
        par_row = []
        par_sum = 0
        for h, t in cursor.fetchall():
            par_row.append(t)
            par_sum += t
        pars = (par_row, par_sum)

        # Other results
        res_rows = []
        index = -1

        query = ("SELECT player, hole, throws, penalty, game_date, game_of_day "
                 "FROM results WHERE course=%s AND player<>'par' "
                 "ORDER BY game_date, game_of_day, player, hole ASC")
        cursor.execute(query, (course_id, ))

        current_game = None
        current_player = None
        row_sum = 0
        row = []
        for p, h, t, b, d, n in cursor.fetchall():
            game = GAME_TEMPLATE % (d, n)
            if current_game != game or p != current_player:
                if current_game:
                    res_rows.append((current_game, current_player, row, row_sum, row_sum-par_sum))
                row_sum = 0
                row = []
                current_game = game
                current_player = p
            if par_row:
                row.append((t, b, t-par_row[h-1]))
            else:
                row.append((t, b, t-3))
            row_sum += t
        res_rows.append((current_game, current_player, row, row_sum, row_sum-par_sum))
        cursor.close()
        return pars, reversed(res_rows)

    def get_latest_games(self):
        query = ("SELECT latest.game_date, latest.game_of_day, co.name, co.id, latest.player, "
                 "latest.res, (latest.res-pars.par) as par "
                 "FROM "
                 "(SELECT sum(throws) as res, player, game_date, game_of_day, course "
                 "FROM results WHERE game_date>(date 'today' -14) AND player<>'par' AND in_play=false "
                 "GROUP BY player, game_date, game_of_day, course) as latest "
                 "JOIN (SELECT sum(throws) as par, course "
                 "FROM results "
                 "WHERE player='par' "
                 "GROUP BY course) as pars "
                 "ON pars.course=latest.course "
                 "JOIN "
                 "(SELECT name, id "
                 "FROM courses) as co "
                 "ON pars.course=co.id "
                 "ORDER BY latest.game_date DESC, latest.game_of_day DESC, co.name, latest.player;")
        cursor = self._cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_course_bests(self):
        query = ("SELECT totals.course, totals.player, min(totals.res) as best, EXTRACT(year FROM totals.game_date) as season "
                "FROM ( "
                "SELECT course, player, game_date, game_of_day, sum(throws) as res "
                "FROM results WHERE player<>'par' "
                "GROUP BY course, player, game_date, game_of_day "
                "ORDER BY course, player, res DESC "
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

    def _check_game_of_day(self, course_id, game_date=None):
        cursor = self._cursor()
        if not game_date:
            game_date = datetime.date.today()
        query = ("SELECT DISTINCT game_of_day FROM results "
                 "WHERE course=%s AND game_date=%s AND in_play=false "
                 "ORDER BY game_of_day DESC LIMIT 1")
        cursor.execute(query, (course_id, game_date))
        game_of_day = cursor.fetchone()
        cursor.close()
        if game_of_day:
            return int(game_of_day[0]) + 1
        else:
            return 1

    def check_curent_hole(self, course_id):
        cursor = self._cursor()
        query = ("SELECT DISTINCT hole FROM results "
                 "WHERE course=%s AND game_date=%s AND in_play=true "
                 "ORDER BY hole DESC LIMIT 1")
        cursor.execute(query, (course_id, datetime.date.today()))
        current_hole = cursor.fetchone()
        cursor.close()
        if current_hole:
            return int(current_hole[0]) + 1
        else:
            return 1

    def add_results(self, course_id, hole, players, throws, penalties, insert_only=False, game_date=None):
        cursor = self._cursor()
        if not insert_only:
            query = ("SELECT * FROM results WHERE course=%s AND in_play=true AND hole=%s")
            cursor.execute(query, (course_id, hole))
        if not insert_only and cursor.fetchall():
            query = ("UPDATE results SET throws=%s, penalty=%s "
                     "WHERE course=%s AND hole=%s AND player=%s AND in_play=true")
            game_of_day = self._check_game_of_day(course_id)
            for i in range(0, len(players)):
                cursor.execute(query, (throws[i], penalties[i], course_id, hole, players[i]))
        else:
            query = ("INSERT INTO results VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            if not game_date:
                game_date = datetime.date.today()
            game_of_day = self._check_game_of_day(course_id, game_date)
            for i in range(0, len(players)):
                cursor.execute(query, (course_id, players[i], hole, throws[i],
                                       penalties[i], game_date, game_of_day, True)
                              )
        self._commit()
        cursor.close()

    def delete_players_game(course_id, player, game_date, game_of_day):
        pass


    def get_probabilities(self, course_id, player):
        cursor = self._cursor()
        query = ("SELECT hole, throws, CAST (count(*) AS FLOAT)/( "
                "SELECT count(*) FROM ( "
                "SELECT DISTINCT game_date, game_of_day "
                "FROM results "
                "WHERE course=%s AND player=%s) as games) "
                "FROM results "
                "WHERE course=%s AND player=%s "
                "GROUP BY hole, throws "
                "ORDER BY hole, throws")
        cursor.execute(query, (course_id, player, course_id, player))
        max_throws = 1
        prev_level = dict()
        new_level = {0: 1}
        current_hole = 0
        for hole, throws, prob in cursor.fetchall():
            if throws > max_throws:
                max_throws = throws
            if current_hole != hole:
                current_hole = hole
                prev_level = new_level
                new_level = dict()

            for res in prev_level:
                new_res = res+throws
                if new_res in new_level:
                    new_level[new_res] += prev_level[res]*prob
                else:
                    new_level[new_res] = prev_level[res]*prob
        cursor.close()
        probs = []
        for x in sorted(new_level.keys()):
            probs.append((x, new_level[x]))
        return probs


    def end_game(self, course_id):
        query = ("UPDATE players SET active=NULL WHERE active=%s")
        cursor = self._cursor()
        cursor.execute(query, (course_id, ))
        self._commit()
        query = ("UPDATE results SET in_play=false WHERE course=%s")
        cursor = self._cursor()
        cursor.execute(query, (course_id, ))
        self._commit()
        cursor.close()


if __name__ == '__main__':
    DB = Database("kopsupullo")
    print DB.get_par(1)
    DB._close_connection()

