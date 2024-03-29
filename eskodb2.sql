
CREATE TYPE terrain AS ENUM ('harju', 'kallio', 'nurmi', 'metsä');
CREATE TYPE hole_type AS ENUM ('suora', 'vasen', 'oikea');
CREATE TYPE elevation_types AS ENUM ('jyrkkä ylämäki', 'ylämäki', 'tasainen', 'alamäki', 'jyrkkä alamäki');
CREATE TYPE weather AS ENUM ('myrsky', 'tuulista', 'tyyni', 'sade', 'talvi');
CREATE TYPE crowds AS ENUM ('hiljaista', 'ruuhkaa', 'tukossa');
CREATE TYPE course_state AS ENUM ('hyvä', 'ok', 'huono', 'karmea');
CREATE TYPE priviledge AS ENUM ('member', 'hallitus', 'admin');


CREATE TABLE course (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    official_name text,
    holes integer CHECK (holes > 0),
    version date DEFAULT CURRENT_DATE,
    description text,
    course_terrain terrain,
    location point,
    map text default NULL,
    town text,
    weekly_day integer default NULL CHECK (weekly_day >= 0 AND weekly_day < 8),
    weekly_time time (0) without time zone default NULL,
    playable boolean default true,
    CONSTRAINT courses_differ UNIQUE(name, holes, version)
);

CREATE TABLE hole (
    id serial PRIMARY KEY,
    length integer default 0,
    height integer default 0,
    description text,
    elevation elevation_types,
    type hole_type,
    hole_terrain terrain,
    par integer default 3,
    ob_area boolean default false,
    mando boolean default false,
    gate boolean default false,
    island boolean default false,
    esko_rating real default NULL
);


CREATE TABLE hole_mapping (
    course integer REFERENCES course(id) ON DELETE CASCADE,
    hole integer REFERENCES hole(id) ON DELETE CASCADE,
    hole_number int,
    PRIMARY KEY (course, hole, hole_number)
);

CREATE TABLE hole_map_item (
    id serial PRIMARY KEY,
    hole integer REFERENCES hole(id) ON DELETE CASCADE,
    type text,
    x int,
    y int
);

CREATE TABLE hole_image (
    id serial PRIMARY KEY,
    hole integer NOT NULL REFERENCES hole(id) ON DELETE CASCADE,
    description text,
    timestamp timestamp default now(),
    image bytea,
    file_type text
);

CREATE TABLE course_image (
    id serial PRIMARY KEY,
    course integer NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    description text,
    timestamp timestamp default now(),
    image bytea,
    file_type text
);

-- Used for EsKo cup 2017
CREATE TABLE cup (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    course integer REFERENCES course(id) ON DELETE CASCADE,
    year integer default EXTRACT(year FROM now()),
    month integer default EXTRACT(month FROM now()),
    max_par integer
);

-- Used for EsKo cup 2018-2021
CREATE TABLE eskocup_course (
    id serial PRIMARY KEY,
    course integer REFERENCES course(id) ON DELETE CASCADE,
    year integer default EXTRACT(year FROM now())
);

CREATE TABLE special_rules (
    id serial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text
);

CREATE TABLE competition (
    id serial PRIMARY KEY,
    competition text NOT NULL,
    course integer REFERENCES course(id) ON DELETE CASCADE,
    start_time timestamp DEFAULT now(),
    end_time timestamp,
    special_rules int REFERENCES special_rules(id) ON DELETE CASCADE DEFAULT NULL,
    rounds integer DEFAULT 1
);

CREATE TABLE game (
    id serial PRIMARY KEY,
    active boolean default true,
    unfinished boolean default false,
    course integer REFERENCES course(id) ON DELETE CASCADE,
    start_time timestamp default now(),
    end_time timestamp,
    game_of_day integer default 1,
    comments text,
    special_rules int REFERENCES special_rules(id) ON DELETE CASCADE DEFAULT NULL,
    steps int default NULL
);
CREATE INDEX ON game (course);


CREATE TABLE player (
    id serial PRIMARY KEY,
    name text unique NOT NULL CHECK (name <> ''),
    member boolean default false,
    user_name text UNIQUE default NULL,
    password text default NULL,
    priviledges priviledge default NULL,
    esko_rating real default NULL,
    active integer
);

CREATE TABLE membership (
    player integer NOT NULL REFERENCES player(id) ON DELETE CASCADE,
    year integer NOT NULL,
    PRIMARY KEY (player, year)
);

CREATE TABLE player_group (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    player integer REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE competition_registration (
    id serial PRIMARY KEY,
    competition integer REFERENCES competition(id) ON DELETE CASCADE,
    player integer REFERENCES player(id) ON DELETE CASCADE,
    game integer REFERENCES game(id) ON DELETE CASCADE
);

CREATE TABLE result (
    id serial PRIMARY KEY,
    game integer REFERENCES game(id) ON DELETE CASCADE,
    player integer REFERENCES player(id) ON DELETE CASCADE,
    hole integer REFERENCES hole(id) ON DELETE CASCADE,
    throws integer default NULL,
    penalty integer default 0,
    approaches integer default NULL,
    puts integer default NULL,
    reported_at timestamp default null
);
