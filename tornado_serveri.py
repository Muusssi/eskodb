import tornado.ioloop
import tornado.web
import tornado.httpserver
import os
import sys
import json
from datetime import date, datetime

import database as db
import models

APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'static'))
TEMPLATES_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'templates'))

def load_config_file(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)



class Application(tornado.web.Application):
    def __init__(self, database, config):


        handlers = [
                (r"/", MainPageHandler),
                (r"/quit", QuitHandler),
                (r"/login", LoginHandler),
                (r"/logout", LogoutHandler),
                (r"/restart/", RestartHandler),
                # (r"/data/(?P<course_id>[^\/]+)/", ResultsHandler),
                (r"/courses", CoursesHandler),
                (r"/course/new/", NewCourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/", CourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/graph", GraphHandler),
                (r"/course/(?P<course_id>[^\/]+)/graphdata", GraphDataHandler),
                (r"/holes/(?P<course_id>[^\/]+)/update", UpdateHolesHandler),
                # (r"/hole_statistics/(?P<course_id>[^\/]+)/(?P<hole>[^\/]+)/", HoleStatisticsHandler),
                # (r"/hole_statistics/(?P<course_id>[^\/]+)/(?P<hole>[^\/]+)/data/", HoleDataHandler),
                (r"/players", PlayersHandler),
                (r"/player/new", NewPlayerHandler),
                (r"/player/(?P<player_id>[^\/]+)/", PlayerHandler),
                (r"/player/(?P<player_id>[^\/]+)/update", UpdatePlayerHandler),
                (r"/games/", GamesHandler),
                (r"/game/new/", NewGameHandler),
                (r"/game/end/(?P<game_id>[^\/]+)/", EndGameHandler),
                (r"/game/(?P<game_id>[^\/]+)/reactivate", ReactivateGameHandler),
                (r"/game/(?P<game_id>[^\/]+)/", GameHandler),
                # (r"/game/data/(?P<course_id>[^\/]+)/", GameResultsHandler),
                # (r"/probabilities/(?P<course_id>[^\/]+)/(?P<player>[^\/]+)/", ProbabilityHandler),
                # (r"/probabilities/data/(?P<course_id>[^\/]+)/(?P<player>[^\/]+)/", ProbabilityDataHandler),
                # (r"/full/(?P<course_id>[^\/]+)/", FullGameHandler),
                (r"/cup/new/", NewCupHandler),
                (r"/eskocup/(?P<year>[^\/]+)/", EsKoCupHandler),
            ]

        settings = dict(
                template_path=TEMPLATES_DIRECTORY,
                static_path=STATIC_DIRECTORY,
                cookie_secret=config['cookie'],
                xsrf_cookies=False,
                login_url="/login",
                debug=True,
            )
        self.database = database
        self.quit_secret = config['quit_secret']
        models.DATABASE = database
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):

    @property
    def required_priviledges(self):
        return (None, 'member', 'hallitus', 'admin')

    @property
    def db(self):
        return self.application.database

    def get_current_user(self):
        user_id = self.get_secure_cookie('user')
        if user_id:
            self.current_user = models.player(user_id)
            return self.current_user
        self.clear_cookie('user')
        return None

    def user_is_authorized(self):
        if self.current_user and self.current_user.priviledges in self.required_priviledges:
            return True
        return False

    def render_unauthorized(self):
        self.render("unauthorized.html",
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

def authorized(method):
    def wrapper(self, *args, **kwargs):
        if self.user_is_authorized():
            method(self, *args, **kwargs)
        else:
            self.render_unauthorized()
    return wrapper


class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html",
                message="",
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        player = None
        players = models.players({'user_name':self.get_argument('user_name')})
        if len(players) == 1:
            player = players[0]
        if player and player.verify(self.get_argument('password', "")):
            self.set_secure_cookie("user", str(player.id))
            self.redirect("/")
        else:
            self.render("login.html",
                    message="Wrong password or user name.",
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect("/")

class QuitHandler(BaseHandler):
    def get(self):
        if self.get_argument('quit', None) == self.application.quit_secret:
            ioloop = tornado.ioloop.IOLoop.instance()
            ioloop.add_callback(ioloop.stop)
        else:
            self.redirect("/")


class MainPageHandler(BaseHandler):
    def get(self):
        self.render("mainpage.html",
                current_season=date.today().year,
                latest=self.db.get_latest_games(),
                bests=self.db.get_course_bests(),
                active_results=self.db.get_active_results(),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class CoursesHandler(BaseHandler):
    def get(self):
        self.render("courses.html",
                courses=models.courses(),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class PlayerHandler(BaseHandler):
    def get(self, player_id):
        self.render("player_stats.html",
                player=models.player(player_id),
                stats=self.db.player_stats(player_id),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )


class CourseHandler(BaseHandler):
    def get(self, course_id):
        selected_player = self.get_argument("player", "")
        holes, hole_dict = models.holes_and_dict({'course':course_id}, 'hole')
        par_sum = sum([hole.par for hole in holes])
        self.render("course.html",
                selected_game_date=self.get_argument("game_date", ""),
                selected_player=selected_player,
                player_dict=models.player_dict(),
                course=models.course(course_id),
                hole_dict=hole_dict,
                holes=holes,
                game_dict=models.game_dict({'course':course_id}),
                result_table=models.results_table({'course':course_id}),
                par_sum=par_sum,
                game_times=self.db.game_times(course_id),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )



class NewCourseHandler(BaseHandler):
    def get(self):
        self.render("new_course.html",
                tittle="Uusi rata",
                terrains=self.db.terrains(),
                course=None,
                message="",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        values = [self.get_argument(field, None) for field in models.Course.fields]
        course = models.Course(values)
        try:
            course.save()
            models.generate_default_holes(course)
            self.redirect("/holes/%s/update" % course.id)
        except Exception as e:
            raise e
            self.render("new_course.html",
                tittle="Uusi rata",
                terrains=self.db.terrains(),
                course=course,
                message="Rata on jo tietokannassa!",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )


class UpdateHolesHandler(BaseHandler):
    def get(self, course_id):
        course = models.course(course_id)
        self.render("update_holes.html",
                terrains=self.db.terrains(),
                hole_types=self.db.hole_types(),
                course=course,
                holes=models.holes({'course':course.id}),
                message="",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self, course_id):
        try:
            course = models.course(course_id)
            values_list = [{} for _ in range(course.holes)]
            for field in models.Hole.fields:
                values = self.get_arguments(field)
                if values:
                    for i in range(len(values_list)):
                        values_list[i][field] = values[i]
            for values in values_list:
                hole = models.Hole(values)
                hole.save()
            self.redirect('/course/%s/' % course.id)
        except Exception as e:
            raise e


class PlayersHandler(BaseHandler):

    @property
    def required_priviledges(self):
        return ('hallitus', 'admin')

    @tornado.web.authenticated
    @authorized
    def get(self):
        self.render("players.html",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class NewPlayerHandler(BaseHandler):
    def get(self):
        self.render("new_player.html",
                tittle="Uusi pelaaja",
                player=None,
                message="",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        values = [self.get_argument(field, None) for field in models.Player.fields]
        player = models.Player(values)
        user = self.get_current_user()
        if user:
            if player.password and player.user_name and user.priviledges == 'admin':
                player.set_password()
            if player.member == None and user.priviledges in ('admin', 'hallitus'):
                player._values['member'] = False
        else:
            player._values['user_name'] = None
            player._values['password'] = None
        if player.save():
            self.redirect("/")
        else:
            self.render("new_player.html",
                tittle="Uusi pelaaja",
                player=player,
                message="Pelaaja on jo tietokannassa!",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class UpdatePlayerHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, player_id):
        player = models.player(player_id)
        self.render("new_player.html",
                tittle="Pelaajan tiedot",
                player=player,
                message="",
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    @tornado.web.authenticated
    def post(self, player_id):
        values = [self.get_argument(field, None) for field in models.Player.fields]
        player = models.Player(values)
        user = self.get_current_user()
        if user:
            if player.password and player.user_name and (
                user.priviledges == 'admin' or int(user.id) == int(player.id)):
                player.set_password()
            elif not (player.password or player.user_name):
                player.values['password'] = None
                player.values['user_name'] = None
            if player.member == None:
                player.values['member'] = False
            if player.save():
                self.redirect("/")

        self.render("new_player.html",
            tittle="Pelaajan tiedot",
            player=player,
            message="Pelaaja on jo tietokannassa!",
            # For template
            course_name_dict=self.db.course_name_dict(),
            active_games=models.games({'active':True}),
            user=self.get_current_user(),
        )

class NewGameHandler(BaseHandler):
    def get(self):
        chosen_course = self.get_argument('course', None)
        self.render("new_game.html",
                message="",
                courses=models.playable_courses(),
                chosen_players=[],
                chosen_course=chosen_course,
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        player_ids = self.get_arguments("player")
        course_id = self.get_argument("course", None)
        if not player_ids:
            self.render("new_game.html",
                    message="Valitse pelaajia!",
                    courses=models.playable_courses(),
                    chosen_players=player_ids,
                    chosen_course=course_id,
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        elif not course_id:
            self.render("new_game.html",
                    message="Valitse rata",
                    courses=models.playable_courses(),
                    chosen_players=player_ids,
                    chosen_course=course_id,
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        else:
            game = models.new_game(course_id, player_ids)
            self.redirect("/game/%s/" % game.id)


class GameHandler(BaseHandler):
    def get(self, game_id):
        game = models.game(game_id)
        course=models.course(game.course)
        holes=models.holes({'course':course.id})
        par_sum = sum([hole.par for hole in holes])
        self.render("game2.html",
                players=models.players({'active':game_id}),
                course=course,
                holes=holes,
                game=game,
                par_sum=par_sum,
                current_hole=self.db.next_hole(game_id),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self, game_id):
        results = self.get_arguments("result")
        if results:
            models.update_game_results(results,
                    self.get_arguments("player"),
                    self.get_arguments("throws"),
                    self.get_arguments("penalty"),
                    self.get_arguments("approaches"),
                    self.get_arguments("puts"),
                )
        data = {'results': self.db.game_results(game_id)}
        if self.get_argument('previous_hole_results', False):
            data['previous'] = self.db.previous_hole_results(game_id)
        self.write(data)

# class FullGameHandler(BaseHandler):
#     def get(self, course_id):
#         self.render("full_game.html",
#                 all_players=models.players(),
#                 course=models.course(course_id),
#                 # For template
#                 course_name_dict=self.db.course_name_dict(),
#                 active_games=models.games({'active':True}),
#                 user=self.get_current_user(),
#             )

#     def post(self, course_id):
#         game_date = self.get_argument("game_date")
#         for p in self.get_arguments("player"):
#             throws = self.get_arguments("%s_throws" % (p, ))
#             penalties = self.get_arguments("%s_penalty" % (p, ))
#             for hole in range(len(throws)):
#                 self.db.add_results(course_id,
#                         hole+1,
#                         [p],
#                         [throws[hole]],
#                         [penalties[hole]],
#                         insert_only=True,
#                         game_date=game_date,
#                     )
#         self.db.end_game(course_id)
#         self.redirect("/course/%s/" % (course_id, ))

class EndGameHandler(BaseHandler):
    def get(self, game_id):
        self.db.end_game(game_id, self.get_argument('unfinished', False))
        self.redirect("/")

class ReactivateGameHandler(BaseHandler):
    def get(self, game_id):
        self.db.reactivate_game(game_id)
        self.redirect("/game/%s/" % (game_id, ))

class GamesHandler(BaseHandler):
    def get(self):
        self.render("games.html",
                games=models.games({}, 'start_time desc'),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )



# class ResultsHandler(BaseHandler):
#     def post(self, course_id):
#         self.write(self.db.get_results(int(course_id)))

#     get = post

# class GameResultsHandler(BaseHandler):
#     def post(self, course_id):
#         self.write(self.db.get_results(int(course_id), True))

#     get = post

# class ProbabilityHandler(BaseHandler):
#     def get(self, course_id, player):
#         self.render("probabilities.html",
#                 course=self.db.get_course(course_id),
#                 player=player,
#                 players=self.db.get_players(),
#                 courses_list=self.db.get_courses(),
#                 actives=self.db.get_courses(True),
#             )

# class ProbabilityDataHandler(BaseHandler):
#     def post(self, course_id, player):
#         course_id = int(course_id)
#         bests = self.db.get_course_bests()
#         season = date.today().year
#         esko_best = bests[course_id]
#         esko_season_best = bests[(course_id, season)]
#         personal_best = bests[(course_id, player)]
#         personal_season_best = bests[(course_id, player, season)]
#         self.write({
#                 'probs': self.db.get_probabilities(course_id, player),
#                 'par': self.db.get_par(course_id),
#                 'esko_best': esko_best,
#                 'esko_season_best': esko_season_best,
#                 'personal_best': personal_best,
#                 'personal_season_best': personal_season_best,
#             })

#     get = post

class RestartHandler(BaseHandler):
    def get(self):
        self.db.reconnect()
        self.redirect("/")


class NewCupHandler(BaseHandler):

    @property
    def required_priviledges(self):
        return ('hallitus', 'admin')

    @tornado.web.authenticated
    @authorized
    def get(self):
        now = datetime.now()
        self.render("cup_form.html",
                message="",
                courses=models.playable_courses(),
                cup=None,
                year=now.year,
                month=now.month,
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    @tornado.web.authenticated
    @authorized
    def post(self):
        values = [self.get_argument(field, None) for field in models.Cup.fields]
        cup = models.Cup(values)
        try:
            cup.save()
            self.redirect("/")
        except:
            now = datetime.now()
            self.render("cup_form.html",
                    message="Virhe!",
                    courses=models.playable_courses(),
                    cup=cup,
                    year=now.year,
                    month=now.month,
                    # For template
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )

class EsKoCupHandler(BaseHandler):

    def get(self, year):
        year = int(year)
        if year == 2017:
            results, points = self.db.cup_results_2017()
            self.render("esko_cup2017.html",
                    cups=models.cups({'name': 'EsKo Cup', 'year':2017}, 'month'),
                    players=models.players({'member':True}, 'name'),
                    course_dict=self.db.course_name_dict(),
                    results=results,
                    points=points,
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        else:
            self.render("esko_cup2018.html",
                    players=models.players({'member':True}, 'name'),
                    results=self.db.cup_results_2018(),
                    cup_courses=models.cup_courses(),
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )


class GraphHandler(BaseHandler):

    def get(self, course_id):
        self.render("graph.html",
                course=models.course(course_id),
                players=self.db.player_with_games_on_course(course_id),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class GraphDataHandler(BaseHandler):

    def post(self, course_id):
        player_id = self.get_argument('player_id', None)
        averaged = self.get_argument('averaged', None)
        self.write(json.dumps(self.db.graphdata(course_id, player_id, averaged)))




# class HoleStatisticsHandler(BaseHandler):
#     def get(self, course_id, hole):
#         self.render("hole_statistics.html",
#                 course=self.db.get_course(course_id),
#                 hole=hole,
#                 courses_list=self.db.get_courses(),
#                 actives=self.db.get_courses(True),
#             )

# class HoleDataHandler(BaseHandler):
#     def post(self, course_id, hole):
#         self.write(self.db.get_hole_statistics(course_id, hole))

#     get = post




if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print "error: missing config file"
        exit(0)
    config = load_config_file(sys.argv[1])
    httpserver = tornado.httpserver.HTTPServer(
            Application(
                    db.Database(config['database'], config['host'], config['user'], config['password']),
                    config,
                )
        )
    httpserver.listen(int(config['port']))
    tornado.ioloop.IOLoop.current().start()
else:
    config = load_config_file('production_config.json')
    webApp = Application(
            db.Database(config['database'], config['host'], config['user'], config['password']),
            config,
        )
    application = tornado.wsgi.WSGIAdapter(webApp)

