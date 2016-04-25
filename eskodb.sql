
CREATE TABLE courses (
    id serial PRIMARY KEY,
    name text NOT NULL CHECK (name <> ''),
    holes integer CHECK (holes > 0),
    version integer DEFAULT 0,
    CONSTRAINT courses_differ UNIQUE(name, holes, version)
);

CREATE TABLE players (
    name text PRIMARY KEY
);

CREATE TABLE results (
    course serial REFERENCES courses(id),
    player text,
    hole integer,
    throws integer,
    penalty integer default 0,
    game_date date default CURRENT_DATE,
    game_of_day integer default 1,
    PRIMARY KEY (course, player, hole, game_date, game_of_day),
    FOREIGN KEY (course) REFERENCES courses (id),
    FOREIGN KEY (player) REFERENCES players(name)
);


INSERT INTO courses(name, holes) VALUES ('Nummela', 18);
INSERT INTO courses(name, holes) VALUES ('Puolari', 14);
INSERT INTO courses(name, holes) VALUES ('Kirkkonummi', 14);
INSERT INTO courses(name, holes) VALUES ('Veikkola', 18);
INSERT INTO courses(name, holes) VALUES ('Oittaa', 12);
INSERT INTO courses(name, holes) VALUES ('Siltamäki', 18);
INSERT INTO courses(name, holes) VALUES ('Kivikko', 18);
INSERT INTO courses(name, holes) VALUES ('Tali', 18);

INSERT INTO players VALUES ('par');
INSERT INTO players VALUES ('Tommi');
INSERT INTO players VALUES ('Oskari');
INSERT INTO players VALUES ('Tapio');
INSERT INTO players VALUES ('Jonne');
INSERT INTO players VALUES ('Antti');
INSERT INTO players VALUES ('Eve');



INSERT INTO results VALUES (1, 'Tommi', 1, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 2, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 3, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 4, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 5, 6, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 6, 7, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 7, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 8, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 9, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 10, 6, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 11, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 12, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 13, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 14, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 15, 3, 1, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 16, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 17, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Tommi', 18, 3, 0, '2016-04-16', 1);


INSERT INTO results VALUES (1, 'Tommi', 1, 2, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 2, 2, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 3, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 4, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 5, 6, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 6, 5, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 7, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 8, 3, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 9, 3, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 10, 5, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 11, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 12, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 13, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 14, 6, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 15, 4, 1, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 16, 4, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 17, 3, 0, '2016-03-30', 1);
INSERT INTO results VALUES (1, 'Tommi', 18, 3, 0, '2016-03-30', 1);


INSERT INTO results VALUES (1, 'Jonne', 1, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 2, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 3, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 4, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 5, 9, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 6, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 7, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 8, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 9, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 10, 6, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 11, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 12, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 13, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 14, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 15, 3, 1, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 16, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 17, 5, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'Jonne', 18, 5, 0, '2016-04-16', 1);


INSERT INTO results VALUES (1, 'par', 1, 2, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 2, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 3, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 4, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 5, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 6, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 7, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 8, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 9, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 10, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 11, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 12, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 13, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 14, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 15, 2, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 16, 4, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 17, 3, 0, '2016-04-16', 1);
INSERT INTO results VALUES (1, 'par', 18, 3, 0, '2016-04-16', 1);



INSERT INTO results VALUES (3, 'par', 1, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 2, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 3, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 4, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 5, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 6, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 7, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 8, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 9, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 10, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 11, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 12, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 13, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'par', 14, 3, 0, '2016-04-20', 1);


INSERT INTO results VALUES (3, 'Tommi', 1, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 2, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 3, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 4, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 5, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 6, 2, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 7, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 8, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 9, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 10, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 11, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 12, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 13, 8, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Tommi', 14, 4, 0, '2016-04-20', 1);

INSERT INTO results VALUES (3, 'Jonne', 1, 7, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 2, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 3, 7, 1, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 4, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 5, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 6, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 7, 7, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 8, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 9, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 10, 6, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 11, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 12, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 13, 6, 0, '2016-04-20', 1);
INSERT INTO results VALUES (3, 'Jonne', 14, 3, 0, '2016-04-20', 1);


INSERT INTO results VALUES (3, 'Tommi', 1, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 2, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 3, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 4, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 5, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 6, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 7, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 8, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 9, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 10, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 11, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 12, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 13, 6, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Tommi', 14, 3, 0, '2016-04-20', 2);

INSERT INTO results VALUES (3, 'Jonne', 1, 5, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 2, 5, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 3, 3, 1, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 4, 6, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 5, 5, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 6, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 7, 5, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 8, 3, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 9, 4, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 10, 5, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 11, 2, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 12, 2, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 13, 6, 0, '2016-04-20', 2);
INSERT INTO results VALUES (3, 'Jonne', 14, 3, 0, '2016-04-20', 2);


INSERT INTO results VALUES (2, 'Tommi', 1, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 2, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 3, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 4, 4, 1, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 5, 4, 1, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 6, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 7, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 8, 2, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 9, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 10, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 11, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 12, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 13, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Tommi', 14, 3, 0, '2016-04-20', 1);

INSERT INTO results VALUES (2, 'Antti', 1, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 2, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 3, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 4, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 5, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 6, 8, 1, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 7, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 8, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 9, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 10, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 11, 4, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 12, 3, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 13, 5, 0, '2016-04-20', 1);
INSERT INTO results VALUES (2, 'Antti', 14, 4, 0, '2016-04-20', 1);




INSERT INTO results VALUES (1, 'Tommi', 1, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 2, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 3, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 4, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 5, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 6, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 7, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 8, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 9, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 10, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 11, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 12, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 13, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 14, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 15, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 16, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 17, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Tommi', 18, 3, 0, '2016-04-24', 1);

INSERT INTO results VALUES (1, 'Oskari', 1, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 2, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 3, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 4, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 5, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 6, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 7, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 8, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 9, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 10, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 11, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 12, 2, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 13, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 14, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 15, 3, 1, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 16, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 17, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Oskari', 18, 3, 0, '2016-04-24', 1);

INSERT INTO results VALUES (1, 'Jonne', 1, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 2, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 3, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 4, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 5, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 6, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 7, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 8, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 9, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 10, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 11, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 12, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 13, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 14, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 15, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 16, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 17, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Jonne', 18, 4, 0, '2016-04-24', 1);

INSERT INTO results VALUES (1, 'Eve', 1, 3, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 2, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 3, 11, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 4, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 5, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 6, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 7, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 8, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 9, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 10, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 11, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 12, 5, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 13, 4, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 14, 7, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 15, 3, 1, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 16, 8, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 17, 6, 0, '2016-04-24', 1);
INSERT INTO results VALUES (1, 'Eve', 18, 6, 0, '2016-04-24', 1);


INSERT INTO results VALUES (8, 'Tommi', 1, 5, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 2, 4, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 3, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 4, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 5, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 6, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 7, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 8, 6, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 9, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 10, 5, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 11, 5, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 12, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 13, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 14, 5, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 15, 6, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 16, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 17, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Tommi', 18, 5, 0, '2016-04-25', 1);












INSERT INTO results VALUES (8, 'Oskari', 1, 7, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 2, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 3, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 4, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 5, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 6, 5, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 7, 7, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 8, 7, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 9, 2, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 10, 6, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 11, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 12, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 13, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 14, 6, 1, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 15, 6, 2, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 16, 3, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 17, 4, 0, '2016-04-25', 1);
INSERT INTO results VALUES (8, 'Oskari', 18, 9, 2, '2016-04-25', 1);








