
CREATE TYPE terrain AS ENUM ('harju', 'kallio', 'nurmi', 'metsä');
CREATE TYPE hole_type AS ENUM ('suora', 'vasen', 'oikea');
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
    CONSTRAINT courses_differ UNIQUE(name, holes, version)
);


CREATE TABLE hole (
    id serial PRIMARY KEY,
    course integer REFERENCES course(id),
    hole integer,
    length integer default 0,
    height integer default 0,
    description text,
    type hole_type,
    hole_terrain terrain,
    par integer default 3,
    ob_area boolean default false,
    mando boolean default false,
    gate boolean default false,
    island boolean default false,
    CONSTRAINT holes_differ UNIQUE(course, hole)
);


CREATE TABLE cup (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    course integer REFERENCES course(id),
    year integer default EXTRACT(year FROM now()),
    month integer default EXTRACT(month FROM now()),
    max_par integer
);


CREATE TABLE game (
    id serial PRIMARY KEY,
    active boolean default true,
    unfinished boolean default false,
    course integer REFERENCES course(id),
    start_time timestamp default now(),
    end_time timestamp,
    game_of_day integer default 1,
    comments text,
    steps int default 0
);


CREATE TABLE player (
    id serial PRIMARY KEY,
    name text unique NOT NULL CHECK (name <> ''),
    member boolean default false,
    user_name text UNIQUE default NULL,
    password text default NULL,
    priviledges priviledge default NULL,
    active integer REFERENCES game(id)
);

CREATE TABLE player_group (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    player integer REFERENCES player(id)
);


CREATE TABLE result (
    id serial PRIMARY KEY,
    game integer REFERENCES game(id),
    player integer REFERENCES player(id),
    hole integer REFERENCES hole(id),
    throws integer default NULL,
    penalty integer default 0,
    approaches integer default NULL,
    puts integer default NULL,
    reported_at timestamp default null
);





-- OLD RESULTS:
-- CREATE TABLE results (
--     course integer,
--     player text,
--     hole integer,
--     throws integer,
--     penalty integer default 0,
--     game_date date default CURRENT_DATE,
--     game_of_day integer default 1,
--     in_play boolean default false
-- );













