
CREATE TABLE courses (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    holes integer CHECK (holes > 0),
    version integer DEFAULT 0,
    CONSTRAINT courses_differ UNIQUE(name, holes, version)
);

CREATE TABLE players (
    name text PRIMARY KEY,
    active integer REFERENCES courses(id) default NULL
);

CREATE TABLE results (
    course serial REFERENCES courses(id),
    player text,
    hole integer,
    throws integer,
    penalty integer default 0,
    game_date date default CURRENT_DATE,
    game_of_day integer default 1,
    in_play boolean default false,
    PRIMARY KEY (course, player, hole, game_date, game_of_day),
    FOREIGN KEY (course) REFERENCES courses (id),
    FOREIGN KEY (player) REFERENCES players(name)
);

-- ALTER TABLE results ADD COLUMN in_play boolean default false;
-- ALTER TABLE players ADD COLUMN active boolean default false;
