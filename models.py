import database as db
from passlib.hash import pbkdf2_sha256

DATABASE = None

WEEK_DAYS = ('maanantai', 'tiistai', 'keskiviikko', 'torstai', 'perjantai', 'lauantai', 'sunnuntai')

class BaseModel(object):

    @property
    def table_name(self):
        return self.__class__.TABLE_NAME

    fields = tuple()
    integer_fields = tuple()

    def __init__(self, values):
        if type(values) is dict:
            self._values = values
        elif type(values) is tuple:
            self._values = dict(zip(self.__class__.fields, values))
        elif type(values) is list:
            self._values = dict(zip(self.__class__.fields, values))
        else:
            raise Exception("Wrong type for model object")
        self._remove_null_fields()
        self._check_fields()
        self._check_types()


    def _remove_null_fields(self):
        for field in self.__class__.fields:
            if field in self._values:
                if self._values[field] == None:
                    del self._values[field]
                elif self._values[field] == "":
                    self._values[field] = None

    def _check_fields(self):
        fields = set(self._values)
        allowed = set(self.__class__.fields)
        additional = fields - allowed
        if additional:
            raise Exception("Additionla fields %s" % additional)

    def _check_types(self):
        for field in self.__class__.integer_fields:
            if field in self._values:
                if self._values[field] not in ('', None):
                    try:
                        self._values[field] = int(self._values[field])
                    except Exception as e:
                        raise e
                else:
                    self._values[field] = None

    def __getattr__(self, attr):
        if attr == 'values':
            return self._values
        if attr not in self.__class__.fields:
            raise Exception("%s missing attribute '%s'" % (self.__class__.__name__, attr))
        if attr in self._values:
            return self._values[attr]
        else:
            return ""

    # def __setattr__(self, attr, value):
    #     if attr == 'values':
    #         for field in value:
    #             self.values[field] = value[field]
    #     elif attr not in self.__class__.fields:
    #         raise Exception("Illegal attribute '%s'" % attr)
    #     else:
    #         self.values[attr] = value


    def save(self):
        try:
            if self.id:
                DATABASE.update_row(self.table_name, self.values, self.id)
            else:
                self.values['id'] = DATABASE.insert_row(self.table_name, self.values)
            return self.id
        except Exception as e:
            raise e


def playable_courses():
    course_list = []
    for values in DATABASE.playable_courses_data(Course.fields):
        course_list.append(Course(values))
    return course_list

def course(course_id):
    row = DATABASE.fetch_rows(Course.TABLE_NAME, Course.fields, {'id':course_id})
    return Course(row[0])

def courses(criteria={}, order_by="name, version"):
    course_list = []
    for values in DATABASE.fetch_rows(Course.TABLE_NAME, Course.fields, criteria, order_by):
        course_list.append(Course(values))
    return course_list

def cup_courses(year):
    additional_where = " id IN (SELECT course FROM eskocup_course WHERE year={}) ".format(int(year))
    course_list = []
    for values in DATABASE.fetch_rows(Course.TABLE_NAME, Course.fields, {}, 'name', additional_where=additional_where):
        course_list.append(Course(values))
    return course_list

class Course(BaseModel):

    TABLE_NAME = 'course'

    fields = (
            'id',
            'name',
            'official_name',
            'holes',
            'version',
            'description',
            'course_terrain',
            'location',
            'map',
            'town',
            'weekly_day',
            'weekly_time',
            'playable',
        )

    integer_fields = (
            'id',
            'holes',
            'weekly_day',
        )

    def weekly_day(self):
        if self.weekly_day:
            WEEK_DAYS[self.weekly_day]
        else:
            return ""

def generate_default_holes(course):
    holes = []
    for hole in range(1, course.holes+1):
        new_hole = Hole({'course':course.id, 'hole':hole})
        new_hole.save()
        holes.append(new_hole)
    return holes

def holes(criteria={}, order_by="hole"):
    hole_list = []
    for values in DATABASE.fetch_rows(Hole.TABLE_NAME, Hole.fields, criteria, order_by):
        hole_list.append(Hole(values))
    return hole_list

class Hole(BaseModel):

    TABLE_NAME = 'hole'

    fields = (
            'id',
            #'course',
            #'hole_number',
            'length',
            'height',
            'description',
            'type',
            'hole_terrain',
            'par',
            'ob_area',
            'mando',
            'gate',
            'island',
        )

    integer_fields = (
            'id',
            #'course',
            #'hole_number',
            'length',
            'height',
            'par',
        )

    def penalty_info(self):
        info = ""
        if self.ob_area:
            info += "OB,"
        if self.mando:
            info += "Mando,"
        if self.gate:
            info += "Portti,"
        if self.island:
            info += "Saari"
        return info


def new_game(course_id, player_ids, special_rules=None):
    game = Game({
            'course':course_id,
            'game_of_day':DATABASE.next_game_of_day(course_id),
            'special_rules':special_rules
        })
    game.save()
    DATABASE.activate_players(player_ids, game.id)
    DATABASE.generate_empty_results(game, player_ids)
    return game

def game(game_id):
    return Game(DATABASE.fetch_rows(Game.TABLE_NAME, Game.fields, criteria={'id':game_id})[0])

def games(criteria={}, order_by=""):
    game_list = []
    for values in DATABASE.fetch_rows(Game.TABLE_NAME, Game.fields, criteria, order_by):
        game_list.append(Game(values))
    return game_list

def game_dict(criteria={}, order_by="", latest=False):
    additional_where = " game.start_time > (date 'today' -14) " if latest else ""
    gamedict = {}
    for values in DATABASE.fetch_rows(
            Game.TABLE_NAME, Game.fields, criteria, order_by,
            additional_where=additional_where
        ):
         game = Game(values)
         gamedict[game.id] = game
    return gamedict

class Game(BaseModel):

    TABLE_NAME = 'game'

    fields = (
            'id',
            'active',
            'course',
            'start_time',
            'end_time ',
            'game_of_day',
            'comments',
            'steps',
            'unfinished',
            'special_rules',
        )

    integer_fields = (
            'id',
            'course',
            'game_of_day',
            'steps',
            'special_rules',
        )

    def label(self):
        return "%s #%s" % (str(self.start_time)[:10], self.game_of_day)


def player(player_id):
    row = DATABASE.fetch_rows(Player.TABLE_NAME, Player.fields, {'id':player_id})
    return Player(row[0])

def players(criteria={}, order_by="name", additional_where=None):
    players_list = []
    for values in DATABASE.fetch_rows(Player.TABLE_NAME, Player.fields, criteria, order_by, additional_where=additional_where):
        players_list.append(Player(values))
    return players_list

def player_dict():
    _player_dict = {}
    for values in DATABASE.fetch_rows(Player.TABLE_NAME, Player.fields):
        player = Player(values)
        _player_dict[player.id] = player
    return _player_dict

class Player(BaseModel):

    TABLE_NAME = 'player'

    fields = (
            'id',
            'name',
            'member',
            'user_name',
            'password',
            'priviledges',
            'active',
        )

    integer_fields = (
            'id',
            'course',
            'active',
        )

    def is_team(self):
        return '&' in self.name

    def set_password(self):
        self._values['password'] = pbkdf2_sha256.encrypt(self.password, rounds=200000, salt_size=16)

    def verify(self, password):
        return pbkdf2_sha256.verify(password, self.password)


def update_game_results(result_ids, player_ids, throws, penalties, approaches, puts):
    for i in range(len(result_ids)):
        res = result(result_ids[i])
        if not res.reported_at:
            res._values['reported_at'] = 'now'
        res._values['throws'] = throws[i] if throws[i] != "" else None
        res._values['penalty'] = penalties[i]
        res._values['approaches'] = approaches[i] if approaches[i] != "" else None
        res._values['puts'] = puts[i] if puts[i] != "" else None
        res.save()

def result(result_id):
    row = DATABASE.fetch_rows(Result.TABLE_NAME, Result.fields, {'id':result_id})
    return Result(row[0])

def results(criteria={}, order_by=""):
    result_list = []
    for values in DATABASE.fetch_rows(Result.TABLE_NAME, Result.fields, criteria, order_by):
        result_list.append(Result(values))
    return result_list

def results_table(criteria={}, latest=False, special_rules=None):
    order_by = "game.start_time desc, game.game_of_day desc, player, hole.hole"
    additional_where = " game.active=false AND game.start_time > (date 'today' -14) " if latest else " game.active=false "
    additional_where += "AND special_rules=%s" % (special_rules, ) if special_rules else "AND special_rules IS NULL "
    result_table = []
    row = []
    previous = None
    join_rule = " JOIN {} on {}.game={}.id JOIN hole ON {}.id={}.hole ".format(
            Game.TABLE_NAME, Result.TABLE_NAME, Game.TABLE_NAME, Hole.TABLE_NAME, Result.TABLE_NAME,
        )
    for values in DATABASE.fetch_rows(
            Result.TABLE_NAME, Result.fields, criteria, order_by, join_rule, additional_where
        ):
        result = Result(values)
        row_name = (result.game, result.player)
        if not previous:
            previous = row_name

        if row_name != previous:
            result_table.append(row)
            previous = row_name
            row = []
        row.append(result)

    if row:
        result_table.append(row)
    return result_table

class Result(BaseModel):

    TABLE_NAME = 'result'

    fields = (
            'id',
            'game',
            'player',
            'hole',
            'throws',
            'penalty',
            'approaches',
            'puts',
            'reported_at',
        )

    integer_fields = (
            'id',
            'game',
            'hole',
            'throws',
            'penalty',
            'approaches',
            'puts',
        )


def cup(cup_id):
    row = DATABASE.fetch_rows(Cup.TABLE_NAME, Cup.fields, {'id':cup_id})
    return Cup(row[0])

def cups(criteria={}, order_by=""):
    cup_list = []
    for values in DATABASE.fetch_rows(Cup.TABLE_NAME, Cup.fields, criteria, order_by):
        cup_list.append(Cup(values))
    return cup_list

class Cup(BaseModel):

    TABLE_NAME = 'cup'

    fields = (
            'id',
            'name',
            'course',
            'month',
            'year',
            'max_par',
        )

    integer_fields = (
            'id',
            'course',
            'month',
            'year',
            'max_par',
        )

def rule_set(rule_id):
    row = DATABASE.fetch_rows(Cup.TABLE_NAME, Cup.fields, {'id':cup_id})
    return Cup(row[0])

def rule_sets(criteria={}, order_by="name"):
    rule_set_list = []
    for values in DATABASE.fetch_rows(RuleSet.TABLE_NAME, RuleSet.fields, criteria, order_by):
        rule_set_list.append(RuleSet(values))
    return rule_set_list

class RuleSet(BaseModel):

    TABLE_NAME = 'special_rules'

    fields = (
            'id',
            'name',
            'description',
        )

    integer_fields = ('id', )

if __name__ == '__main__':

    DATABASE = db.Database('foo')
    player = player(1)
    player._values['password'] = 'foo'
    player._values['user_name'] = 'tommi'
    player.set_password()
    player.save()


