import psycopg2
import models
import database as db


DATABASE = 'test_eskodb'
PASSWORD = 'password'
USER = 'esko'

def get_player_by_name(name):
    players = models.players({'name': name})
    if len(players) == 1:
        return players[0].id
    else:
        return None

def initialize_test_database():
    models.DATABASE = db.Database(DATABASE, PASSWORD)
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
    visitor = models.Player({'name': 'Vistor'})
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






