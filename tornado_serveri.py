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
                (r"/courses", CoursesHandler),
                (r"/course/new/", NewCourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/", CourseHandler),
                (r"/course/(?P<course_id>[^\/]+)/graph", GraphHandler),
                (r"/course/(?P<course_id>[^\/]+)/graphdata", GraphDataHandler),
                (r"/holes/(?P<course_id>[^\/]+)/update", UpdateHolesHandler),
                (r"/players", PlayersHandler),
                (r"/player/new", NewPlayerHandler),
                (r"/player/(?P<player_id>[^\/]+)/", PlayerHandler),
                (r"/player/(?P<player_id>[^\/]+)/update", UpdatePlayerHandler),
                (r"/games/", GamesHandler),
                (r"/game/new/", NewGameHandler),
                (r"/game/end/(?P<game_id>[^\/]+)/", EndGameHandler),
                (r"/game/(?P<game_id>[^\/]+)/reactivate", ReactivateGameHandler),
                (r"/game/(?P<game_id>[^\/]+)/", GameHandler),
                (r"/cup/new/", NewCupHandler),
                (r"/eskocup/(?P<year>[^\/]+)/", EsKoCupHandler),
                (r"/hole/(?P<hole_id>[^\/]+)/map/edit", EditHoleMapHandler),
                (r"/rule/new", NewRuleHandler),

                (r"/game_stats", StatsTableHandler),

                (r"/data/players/", PlayersDataHandler),
                (r"/data/game_stats/", GameStatDataHandler),
                (r"/data/courses/", CoursesDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/$", CourseDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/holes/", HolesDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/rule_sets/", RuleSetsDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/game_times/", GameTimesDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/results/", ResultsDataHandler),
                (r"/data/course/(?P<course_id>[0-9]+)/upload_image/", CourseImageUploadHandler),
                (r"/data/course_image/(?P<image_id>[0-9]+)/", CourseImageHandler),
                (r"/data/hole/(?P<hole_id>[0-9]+)/", HoleDataHandler),
                (r"/data/hole/(?P<hole_id>[0-9]+)/map/", HoleMapDataHandler),
                (r"/data/hole/(?P<hole_id>[0-9]+)/upload_image/", HoleImageUploadHandler),
                (r"/data/hole_image/(?P<image_id>[0-9]+)/", HoleImageHandler),
                (r"/data/game/(?P<game_id>[0-9]+)/", GameDataHandler),
                (r"/data/game/(?P<game_id>[0-9]+)/previous_results/", PreviousResultsDataHandler),
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

    def get_bool_argument(self, name, default):
        value = self.get_argument(name, None)
        if value in ('False', 'false', 'f', 'no'):
            return False
        elif value in ('True', 'true', 't', 'yes'):
            return True
        else:
            return default

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
        course=models.course(course_id)
        self.render("course.html",
                selected_game_date=self.get_argument("game_date", ""),
                selected_player=selected_player,
                course=models.course(course_id),
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
            course_id = course.save()
            self.db.generate_default_holes(course.id, course.holes)
            self.redirect("/holes/%s/update" % course.id)
        except Exception as e:
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
        self.render("update_holes.html",
                terrains=self.db.terrains(),
                hole_types=self.db.hole_types(),
                course=models.course(course_id),
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
                rule_sets=models.rule_sets(),
                chosen_players=[],
                chosen_course=chosen_course,
                special_rules=None,
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        player_ids = self.get_arguments("player")
        course_id = self.get_argument("course", None)
        special_rules = self.get_argument("special_rules", None)
        if not player_ids:
            self.render("new_game.html",
                    message="Valitse pelaajia!",
                    courses=models.playable_courses(),
                    rule_sets=models.rule_sets(),
                    chosen_players=player_ids,
                    chosen_course=course_id,
                    special_rules=special_rules,
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
                    rule_sets=models.rule_sets(),
                    chosen_players=player_ids,
                    chosen_course=course_id,
                    special_rules=special_rules,
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        else:
            game = models.new_game(course_id, player_ids, special_rules)
            self.redirect("/game/{}/".format(int(game.id)))


class GameHandler(BaseHandler):

    def get(self, game_id):
        game = models.game(game_id)
        course=models.course(game.course)
        self.render("game.html",
                players=models.players({'active':game_id}),
                course=course,
                game=game,
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self, game_id):
        results = self.get_arguments("result")
        if results:
            self.db.update_game_results(results,
                    self.get_arguments("player"),
                    self.get_arguments("throws"),
                    self.get_arguments("penalty"),
                    self.get_arguments("approaches"),
                    self.get_arguments("puts"),
                )
        self.write({'results': self.db.game_results(game_id)})

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

class RestartHandler(BaseHandler):
    def get(self):
        self.db.reconnect()
        self.redirect("/")

class StatsTableHandler(BaseHandler):
    def get(self):
        self.render('api_table.html',
                courses=models.courses(),
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

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
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )

class EsKoCupHandler(BaseHandler):

    def get(self, year):
        year = int(year)
        membership_filter = "id IN (SELECT player FROM membership WHERE year={})"
        if year == 2017:
            results, points = self.db.cup_results_2017()
            self.render("esko_cup2017.html",
                    cups=models.cups({'name': 'EsKo Cup', 'year':2017}, 'month'),
                    players=models.players({}, 'name', additional_where=membership_filter.format(2017)),
                    course_dict=self.db.course_name_dict(),
                    results=results,
                    points=points,
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        elif year == 2018:
            first_stage_results = self.db.cup_results_2018(True)
            self.render("esko_cup2018.html",
                    players=models.players({}, 'name', additional_where=membership_filter.format(2018)),
                    results=self.db.cup_results_2018(),
                    first_stage_results=first_stage_results,
                    handicap_results=self.db.cup_results_2018_with_handicaps(first_stage_results),
                    cup_courses=models.cup_courses(2018),
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )
        else:
            first_stage_results, first_stage_points = self.db.cup_results_2019(True)
            overall_results, _ = self.db.cup_results_2019()
            self.render("esko_cup2019.html",
                    players=models.players({}, 'name', additional_where=membership_filter.format(2019)),
                    results=overall_results,
                    first_stage_results=first_stage_results,
                    first_stage_points=first_stage_points,
                    #handicap_results=self.db.cup_results_2019_with_handicaps(first_stage_results),
                    cup_courses=models.cup_courses(2019),
                    # For template
                    all_players=models.players(),
                    course_name_dict=self.db.course_name_dict(),
                    active_games=models.games({'active':True}),
                    user=self.get_current_user(),
                )

class EditHoleMapHandler(BaseHandler):
    def get(self, hole_id):
        self.render('hole_map.html',
                hole_id=hole_id,
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

class NewRuleHandler(BaseHandler):
    def get(self):
        self.render("new_rules.html",
                message="",
                name='',
                description='',
                # For template
                all_players=models.players(),
                course_name_dict=self.db.course_name_dict(),
                active_games=models.games({'active':True}),
                user=self.get_current_user(),
            )

    def post(self):
        name = self.get_argument('name', '')
        description = self.get_argument('description', '')
        if name:
            try:
                self.db.new_rule_set(name, description)
                self.redirect('/')
                return
            except Exception as e:
                message="Nimi on varattu."
        else:
            message="Nimi puuttuu."

        self.render("new_rules.html",
            message=message,
            name=name,
            description=description,
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


class GameStatDataHandler(BaseHandler):
    def get(self):
        self.write(self.db.throw_stats(self.request.arguments))
    post = get

class PlayersDataHandler(BaseHandler):
    def get(self):
        self.write(self.db.players_data(self.get_bool_argument('as_dict', False)))

class CourseDataHandler(BaseHandler):
    def get(self, course_id):
        self.write(self.db.course_data(course_id))

class CoursesDataHandler(BaseHandler):
    def get(self):
        self.write(self.db.courses_data(self.get_bool_argument('as_dict', False)))

class HolesDataHandler(BaseHandler):
    def get(self, course_id):
        self.write({'holes': self.db.holes_data(course_id, self.get_bool_argument('as_dict', False))})

class HoleDataHandler(BaseHandler):
    def get(self, hole_id):
        self.write(self.db.hole_data(hole_id))

class ImageUploadHandler(BaseHandler):
    def posted_image_data(self):
        fileinfo = self.request.files['filearg'][0]
        desc = self.get_argument('description')
        fname = fileinfo['filename']
        extension = fname.split('.')[-1]
        if extension in ('png', 'jpg', 'jpeg'):
            return desc, fileinfo['body'], extension
        else:
            return desc, None, extension

class HoleImageUploadHandler(ImageUploadHandler):
    def get(self, hole_id):
        self.render('upload_image.html',
                message="",
                linked_to="hole id {}".format(hole_id),
                default_desc="Opaste",
                redirect_to=self.get_argument('redirect_to', '/')
            )

    def post(self, hole_id):
        desc, data, file_type = self.posted_image_data()
        if data:
            self.db.store_hole_image(hole_id, desc, data, file_type)
            self.redirect(self.get_argument('redirect_to', '/'))
        else:
            self.render('upload_image.html',
                    message="Error: Unsupported filetype '{}'! Only PNG or JPG are supported.".format(file_type),
                    linked_to="hole id {}".format(hole_id),
                    default_desc=desc,
                    redirect_to=self.get_argument('redirect_to', '/')
                )

class CourseImageUploadHandler(ImageUploadHandler):
    def get(self, course_id):
        course = models.course(course_id)
        self.render('upload_image.html',
                message="",
                linked_to="{} {}".format(course.name, course.holes),
                default_desc="Ratakartta",
                redirect_to=self.get_argument('redirect_to', '/')
            )

    def post(self, course_id):
        desc, data, file_type = self.posted_image_data()
        if data:
            self.db.store_course_image(course_id, desc, data, file_type)
            self.redirect(self.get_argument('redirect_to', '/'))
        else:
            self.render('upload_image.html',
                    message="Error: Unsupported filetype '{}'! Only PNG or JPG are supported.".format(file_type),
                    linked_to="{} {}".format(course.name, course.holes),
                    default_desc=desc,
                    redirect_to=self.get_argument('redirect_to', '/')
                )

class HoleImageHandler(BaseHandler):
    def get(self, image_id):
        image_data, file_type = self.db.get_hole_image(image_id)
        self.set_header('Content-Type', 'image/{}'.format(file_type))
        self.write(bytes(image_data))

class CourseImageHandler(BaseHandler):
    def get(self, image_id):
        image_data, file_type = self.db.get_course_image(image_id)
        self.set_header('Content-Type', 'image/{}'.format(file_type))
        self.write(bytes(image_data))

class HoleMapDataHandler(BaseHandler):
    def get(self, hole_id):
        self.write(self.db.hole_map_data(hole_id))

    def post(self, hole_id):
        data = json.loads(self.request.body)
        self.db.update_map_data(hole_id, data['items'])

class GameDataHandler(BaseHandler):
    def get(self, game_id):
        self.write(self.db.game_data(game_id))

class GameTimesDataHandler(BaseHandler):
    def get(self, course_id):
        self.write({'rules': self.db.game_times_data(course_id)})

class PreviousResultsDataHandler(BaseHandler):
    def get(self, game_id):
        self.write(self.db.previous_hole_stats(game_id))

class ResultsDataHandler(BaseHandler):
    def get(self, course_id):
        self.write(self.db.course_results_data(course_id))

class RuleSetsDataHandler(BaseHandler):
    def get(self, course_id):
        self.write({'rule_sets': self.db.course_rule_sets(course_id)})


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("error: missing config file")
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

