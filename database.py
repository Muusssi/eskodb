import psycopg2

GAME_TEMPLATE = "%s #%s"

class Database(object):

    def __init__(self, pw):
        self._conn = psycopg2.connect(
                "dbname='eskodb' user='esko' host='localhost' password='%s'" %
                (pw, )
            )

    def _cursor(self):
        return self._conn.cursor()

    def _close_connection(self):
        self._conn.close()

    def get_players(self):
        query = ("SELECT name FROM players ORDER BY name")
        cursor = self._cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        cursor.close()
        return res


    def get_courses(self):
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

    def get_results(self, course_id):
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
        par_row = [None for k in range(holes+3)]
        par_sum = 0
        for h, t in cursor.fetchall():
            par_row[1+h] = t
            par_sum += t
        par_row[0] = ''
        par_row[1] = 'par'
        par_row[holes+2] = par_sum
        results['rows'] = [par_row]

        # Other results
        res_rows = []
        query = ("SELECT player, hole, throws, penalty, game_date, game_of_day "
                 "FROM results WHERE course=%s AND player<>'par' "
                 "ORDER BY game_date, game_of_day, player, hole ASC")
        cursor.execute(query, (course_id, ))
        index = -1
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




if __name__ == '__main__':
    db = Database("kopsupullo")
    res = db.get_results(1)
    print res['rows']
    db._close_connection()

