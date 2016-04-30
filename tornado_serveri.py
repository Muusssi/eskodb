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
                (r"/$", MainPageHandler),
                (r"/data/(?P<course_id>[^\/]+)/$", DataHandler),
                (r"/course/new/$", NewCourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/$", CourseHandler),
                (r"/player/new/$", NewPlayerHandler),

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
                players = self.db.get_players(),
                courses = self.db.get_courses(),
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


class DataHandler(BaseHandler):
    def post(self, course_id):
        self.write(self.db.get_results(int(course_id)))

    get = post


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print "error: missing password"
        exit(0)
    httpserver = tornado.httpserver.HTTPServer(Application(db.Database(sys.argv[1])))
    httpserver.listen(8888)
    tornado.ioloop.IOLoop.current().start()

