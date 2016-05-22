import tornado.ioloop
import tornado.web
import tornado.httpserver
import os
import database as db
import sys

APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'static'))
TEMPLATES_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'templates'))



class Application(tornado.web.Application):
    def __init__(self, database):
        handlers = [
                (r"/", MainPageHandler),
                (r"/restart/", RestartHandler),
                (r"/data/(?P<course_id>[^\/]+)/", ResultsHandler),
                (r"/course/new/", NewCourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/", CourseHandler),
                #(r"/course/(?P<course_id>[^\/]+)/statistics/", CourseStatisticsHandler),
                (r"/player/new/", NewPlayerHandler),
                (r"/game/new/", NewGameHandler),
                (r"/game/end/(?P<course_id>[^\/]+)/", EndGameHandler),
                (r"/game/(?P<course_id>[^\/]+)/", GameHandler),
                (r"/game/data/(?P<course_id>[^\/]+)/", GameResultsHandler),
                (r"/full/(?P<course_id>[^\/]+)/", FullGameHandler),

            ]

        settings = dict(
                template_path=TEMPLATES_DIRECTORY,
                static_path=STATIC_DIRECTORY,
                debug=True,
            )

        self.database = database
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.database


class MainPageHandler(BaseHandler):
    def get(self):
        self.render("mainpage.html",
                players=self.db.get_players(),
                courses=self.db.get_courses(),
                actives= self.db.get_courses(True),
            )

class CourseHandler(BaseHandler):
    def get(self, course_id):
        self.render("course.html",
                course=self.db.get_course(course_id),
            )

class NewCourseHandler(BaseHandler):
    def get(self):
        self.render("new_course.html",
                message="",
            )

    def post(self):
        if self.db.add_course(self.get_argument("name"), self.get_argument("holes")):
            self.redirect("/")
        else:
            self.render("new_course.html",
                message="Rata on jo tietokannassa!",
            )

class NewPlayerHandler(BaseHandler):
    def get(self):
        self.render("new_player.html",
                message="",
            )

    def post(self):
        if self.db.add_player(self.get_argument("name")):
            self.redirect("/")
        else:
            self.render("new_player.html",
                message="Pelaaja on jo tietokannassa!",
            )

class NewGameHandler(BaseHandler):
    def get(self):
        self.render("new_game.html",
                message="",
                players=self.db.get_players(),
                courses=self.db.get_courses(),
            )

    def post(self):
        players = self.get_arguments("player")
        course_id = self.get_argument("course")
        if players:
            self.db.activate_players(players, course_id)
            self.redirect("/game/%s/" % (course_id, ))
        else:
            self.render("new_game.html",
                    message="Pelaajia on valittava",
                    players=self.db.get_players(),
                    courses=self.db.get_courses(),
                )

class GameHandler(BaseHandler):
    def get(self, course_id):
        self.render("game.html",
                players=self.db.get_players(course_id),
                course=self.db.get_course(course_id),
                current_hole=self.db.check_curent_hole(course_id),
            )

    def post(self, course_id):
        self.db.add_results(course_id,
                self.get_argument("hole"),
                self.get_arguments("player"),
                self.get_arguments("throws"),
                self.get_arguments("penalty"),
            )
        self.write(self.db.get_results(int(course_id), True))

class FullGameHandler(BaseHandler):
    def get(self, course_id):
        self.render("full_game.html",
                players=self.db.get_players(),
                course=self.db.get_course(course_id),
                #current_hole=self.db.check_curent_hole(course_id),
            )

    def post(self, course_id):
        for p in self.get_arguments("player"):
            throws = self.get_arguments("%s_throws" % (p, ))
            penalties = self.get_arguments("%s_penalty" % (p, ))
            for hole in range(len(throws)):
                self.db.add_results(course_id,
                        hole+1,
                        [p],
                        [throws[hole]],
                        [penalties[hole]],
                        insert_only=True,
                    )
        self.db.end_game(course_id)
        self.redirect("/course/%s/" % (course_id, ))

class EndGameHandler(BaseHandler):
    def get(self, course_id):
        self.db.end_game(course_id)
        self.redirect("/course/%s/" % (course_id, ))


class ResultsHandler(BaseHandler):
    def post(self, course_id):
        self.write(self.db.get_results(int(course_id)))

    get = post

class GameResultsHandler(BaseHandler):
    def post(self, course_id):
        self.write(self.db.get_results(int(course_id), True))

    get = post

class RestartHandler(BaseHandler):
    def get(self):
        self.db.reconnect()
        self.redirect("/")

class CourseStatisticsHandler(BaseHandler):
    pass


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print "error: missing password"
        exit(0)

    httpserver = tornado.httpserver.HTTPServer(Application(db.Database(sys.argv[1])))
    httpserver.listen(8888)
    tornado.ioloop.IOLoop.current().start()

