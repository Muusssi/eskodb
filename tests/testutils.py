import json
import random
import datetime

import psycopg2

import models
import database as db


def load_config_file(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def get_player_by_name(name):
    players = models.players({'name': name})
    if len(players) == 1:
        return players[0]
    else:
        return None

def get_course_by_name(name):
    courses = models.courses({'name': name})
    if len(courses) == 1:
        return courses[0]
    else:
        return None

def get_active_games_by_course_id(course_id):
    return models.games({'course': course_id, 'active': True})

def get_results_by_game_id(game_id):
    return models.results({'game': game_id}, 'hole')

def check_results_as_expected(results, expected):
    for i in range(len(results)):
        if expected[i] == 'None':
            if results[i].throws:
                return False
        elif str(results[i].throws) != str(expected[i]):
            return False
    return True

def initialize_test_database():
    config = load_config_file("tests/test_config.json")
    database = db.Database(
            config['database'],
            config['host'],
            config['user'],
            config['password'],
        )
    models.DATABASE = database

    # Initialize courses
    course = models.Course({'name': 'A-Rata', 'holes': 18})
    course.save()
    database.generate_default_holes(course.id, course.holes)
    course2 = models.Course({'name': 'B-Rata', 'holes': 12})
    course2.save()
    database.generate_default_holes(course2.id, course2.holes)
    short_course = models.Course({'name': 'Lyhyt rata', 'holes': 6})
    short_course.save()
    database.generate_default_holes(short_course.id, short_course.holes)

    # Initialize players
    visitor = models.Player({'name': 'Visitor'})
    visitor.save()
    member = models.Player({'name': 'Club member', 'member': True})
    member.save()
    user = models.Player({
            'name': 'ordinary user',
            'member': True,
            'priviledges': 'member',
            'user_name': 'ordinary',
            'password': 'somewhatsecret',
        })
    user.set_password()
    user.save()
    admin = models.Player({
            'name': 'Admin',
            'member': True,
            'priviledges': 'admin',
            'user_name': 'admin',
            'password': 'supersecret',
        })
    admin.set_password()
    admin.save()

    # Cups
    cup1 = models.Cup({
            'name': 'EsKo Cup',
            'month': 6,
            'year': 2017,
            'course': course.id,
            'max_par': 15,
        })
    cup1.save()
    cup2 = models.Cup({
            'name': 'EsKo Cup',
            'month': 7,
            'year': 2017,
            'course': course2.id,
            'max_par': 20,
        })
    cup2.save()

    # Special rules
    rule_set1 = models.RuleSet({
            'name': "Shotput",
            'description': "Instead of disc playing with shotputs.",
        })
    rule_set1.save()

    generate_game_and_results(database, course.id, [member.id], game_time=datetime.timedelta(minutes=90))
    generate_game_and_results(database, course.id, [member.id, visitor.id], game_time=datetime.timedelta(minutes=110))
    generate_game_and_results(database, course.id, [member.id], game_time=datetime.timedelta(minutes=95))

def generate_game_and_results(database, course_id, player_ids, special_rules=None, game_time=None):
    game = models.new_game(course_id, player_ids, special_rules)
    result_data = database.game_results(game.id)
    hole_count = len(result_data[0]['results'])
    for hole_index in range(hole_count):
        result_ids = []
        player_ids = []
        for player_data in result_data:
            player_ids.append(player_data['player_id'])
            result_ids.append(player_data['results'][hole_index]['id'])
        database.update_game_results(
                result_ids,
                player_ids,
                [random.choice([2,3,3,3,3,4,4,5]) for _ in range(len(player_ids))],
                [random.choice([0,0,0,0,0,0,1,1]) for _ in range(len(player_ids))],
                ['' for _ in range(len(player_ids))],
                ['' for _ in range(len(player_ids))],
            )
    database.end_game(game.id, False)
    if game_time:
        database.set_game_time(game.id, game_time)
    return game



if __name__ == '__main__':
    initialize_test_database()



