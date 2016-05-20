import psycopg2
import datetime

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

    def get_course(self, id):
        query = ("SELECT name, holes, id FROM courses WHERE id=%s")
        cursor = self._cursor()
        cursor.execute(query, (id, ))
        res = cursor.fetchone()
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
                if b>0:
                    penalty = ''
                    for k in range(b):
                        penalty += '*'
                    res_rows[index][1+h] = {'v':t, 'f':str(t)+penalty }
                else:
                    res_rows[index][1+h] = t
                res_rows[index][holes+2] += t

        results['rows'].extend(reversed(res_rows))

        cursor.close()
        return results

    def _check_game_of_day(self, course_id):
        cursor = self._cursor()
        query = ("SELECT DISTINCT game_of_day FROM results "
                 "WHERE course=%s AND game_date=%s AND in_play=false "
                 "ORDER BY game_of_day DESC LIMIT 1")
        cursor.execute(query, (course_id, datetime.date.today()))
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

    def add_results(self, course_id, hole, players, throws, penalties):
        cursor = self._cursor()
        query = ("SELECT * FROM results WHERE course=%s AND in_play=true AND hole=%s")
        cursor.execute(query, (course_id, hole))
        if cursor.fetchall():
            query = ("UPDATE results SET throws=%s, penalty=%s "
                     "WHERE course=%s AND hole=%s AND player=%s AND in_play=true")
            game_of_day = self._check_game_of_day(course_id)
            for i in range(0, len(players)):
                cursor.execute(query, (throws[i], penalties[i], course_id, hole, players[i]))
        else:
            query = ("INSERT INTO results VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            game_of_day = self._check_game_of_day(course_id)
            for i in range(0, len(players)):
                cursor.execute(query, (course_id, players[i], hole, throws[i],
                        penalties[i], datetime.date.today(), game_of_day, True)
                    )
        self._commit()
        cursor.close()


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
    db = Database("kopsupullo")
    print db.get_results(5)
    db._close_connection()

