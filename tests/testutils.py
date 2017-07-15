import psycopg2
import models
import database as db
import json

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

def get_games_by_course_id(course_id):
    return models.games({'course': course_id})

def initialize_test_database():
    config = load_config_file("tests/test_config.json")
    models.DATABASE = db.Database(
            config['database'],
            config['host'],
            config['user'],
            config['password'],
        )
    # Initialize courses
    course = models.Course({'name': 'A-Rata', 'holes': 18})
    course.save()
    models.generate_default_holes(course)
    course2 = models.Course({'name': 'B-Rata', 'holes': 12})
    course2.save()
    models.generate_default_holes(course2)
    course3 = models.Course({'name': 'C-Rata', 'holes': 6})
    course3.save()
    models.generate_default_holes(course3)

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
            'name': 'Mr Admin',
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






