    -- CREATE DATABASE patools17 WITH ENCODING = 'LATIN1';
    -- createlang plpgsql patest | CREATE LANGUAGE plpgqsl


    CREATE TABLE updates (
     id serial ,
     tick smallint UNIQUE,
     planets smallint,
     galaxies smallint,
     alliances smallint,
     timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
     PRIMARY KEY (id)
    );

    INSERT INTO updates VALUES (-1,-1,-1,-1,-1);

    CREATE TABLE planet_canon (
     id serial,
     planetname varchar(20) NOT NULL,
     rulername varchar(20) NOT NULL,
     active boolean NOT NULL DEFAULT TRUE,
     PRIMARY KEY(id),
     UNIQUE (rulername,planetname)
    );

    CREATE TABLE planet_dump (
     tick smallint REFERENCES updates (tick),
     x smallint,
     y smallint,
     z smallint,
     planetname varchar(20) NOT NULL,
     rulername varchar(20) NOT NULL,
     race char(3) NOT NULL CHECK (race in ('Ter','Cat','Xan','Zik','Etd')),
     size smallint NOT NULL,
     score integer NOT NULL,
     value integer NOT NULL,
     score_rank smallint NOT NULL,
     value_rank smallint NOT NULL,
     size_rank smallint NOT NULL,
     xp integer NOT NULL,
     xp_rank smallint NOT NULL,
     idle smallint NOT NULL DEFAULT 0,
     vdiff integer NOT NULL DEFAULT 0,
     id integer NOT NULL REFERENCES planet_canon(id),
     PRIMARY KEY(tick, x, y, z),
     FOREIGN KEY(rulername,planetname) REFERENCES planet_canon (rulername,planetname)
    );

    CREATE TABLE galaxy_canon (
     id serial,
     x smallint,
     y smallint,
     active boolean NOT NULL DEFAULT TRUE,
     PRIMARY KEY(id),
     UNIQUE(x,y)
    );

    CREATE TABLE galaxy_dump (
     tick smallint REFERENCES updates (tick),
     x smallint,
     y smallint,
     name varchar(64) NOT NULL,
     size int NOT NULL,
     score bigint NOT NULL,
     value bigint NOT NULL,
     score_rank smallint NOT NULL,
     value_rank smallint NOT NULL,
     size_rank smallint NOT NULL,
     xp integer NOT NULL,
     xp_rank smallint NOT NULL,
     id integer NOT NULL REFERENCES galaxy_canon(id),
     PRIMARY KEY(tick, x, y),
     FOREIGN KEY(x,y) REFERENCES galaxy_canon (x,y)
    );

    CREATE TABLE alliance_canon (
     id serial,
     name varchar(20) UNIQUE,
     active boolean NOT NULL DEFAULT TRUE,
     PRIMARY KEY(id)
    );

    CREATE TABLE alliance_dump (
     tick smallint REFERENCES updates (tick),
     name varchar(20) NOT NULL REFERENCES alliance_canon (name),
     size int NOT NULL,
     members smallint NOT NULL,
     score bigint NOT NULL,
     score_rank smallint NOT NULL,
     size_rank smallint NOT NULL,
     members_rank smallint NOT NULL,
     score_avg int NOT NULL,
     size_avg smallint NOT NULL,
     score_avg_rank smallint NOT NULL,
     size_avg_rank smallint NOT NULL,
     id integer NOT NULL REFERENCES alliance_canon(id),
     PRIMARY KEY(tick, name)
    );

    CREATE INDEX planet_dump_tick_index ON planet_dump(tick);
    CREATE INDEX planet_dump_id_index ON planet_dump(id);
    CREATE INDEX planet_dump_rn_index ON planet_dump(rulername);
    CREATE INDEX planet_dump_pn_index ON planet_dump(planetname);


    CREATE INDEX galaxy_dump_tick_index ON galaxy_dump(tick);

    CREATE INDEX galaxy_dump_id_index ON galaxy_dump(id);

    CREATE INDEX alliance_dump_tick_index ON alliance_dump(tick);

    CREATE INDEX alliance_dump_id_index ON alliance_dump(id);



    CREATE TABLE user_list (
        id SERIAL PRIMARY KEY,
        pnick VARCHAR(15) NOT NULL,
        alias_nick VARCHAR(15),
        sponsor VARCHAR(15),
        passwd CHAR(32),
        userlevel INTEGER NOT NULL,
	posflags VARCHAR(30),
	negflags VARCHAR(30),
	planet_id integer REFERENCES planet_canon(id) ON DELETE CASCADE,
	stay BOOLEAN DEFAULT FALSE,
	invites smallint NOT NULL DEFAULT 0 CHECK (invites >= 0),
	quit smallint NOT NULL DEFAULT 0,
	phone VARCHAR(48),
	pubphone BOOLEAN NOT NULL DEFAULT FALSE, 
        available_cookies smallint NOT NULL DEFAULT 0,
        carebears integer NOT NULL DEFAULT 0,
        last_cookie_date TIMESTAMP DEFAULT NULL,
        fleetcount integer NOT NULL DEFAULT 0,
        fleetcomment VARCHAR(512) NOT NULL DEFAULT '',
        fleetupdated integer NOT NULL DEFAULT 0,
	salt varchar(4) NOT NULL DEFAULT SUBSTRING(CAST(RANDOM() AS VARCHAR) FROM 3 FOR 4)
);

CREATE TABLE cookie_log (
       id SERIAL PRIMARY KEY,
       log_time TIMESTAMP NOT NULL DEFAULT NOW(),
       year_number smallint NOT NULL,
       week_number smallint NOT NULL,
       howmany integer NOT NULL,
       giver integer REFERENCES user_list(id),
       receiver integer REFERENCES user_list(id)
);
       

CREATE TABLE user_fleet (
       id SERIAL PRIMARY KEY,
       user_id integer REFERENCES user_list(id),
       ship varchar(30) NOT NULL,
       ship_count integer
);

CREATE TABLE fleet_log (
       id SERIAL PRIMARY KEY,
       taker_id integer REFERENCES user_list(id),
       user_id integer REFERENCES user_list(id),
       ship varchar(30) NOT NULL,
       ship_count integer,
       tick integer REFERENCES updates(tick) DEFAULT max_tick()
);


CREATE UNIQUE INDEX user_list_pnick_case_insensitive_index ON user_list(LOWER(pnick));

-- UNCOMMENT THIS IF YOU WANT TO INSERT A SUPERUSER ON DB CREATION
--INSERT INTO user_list (pnick,sponsor,userlevel) VALUES ('jester','Munin',1000);

CREATE TABLE channel_list (
	id SERIAL PRIMARY KEY,
	chan VARCHAR(150) NOT NULL UNIQUE,
        userlevel INTEGER NOT NULL,
	maxlevel INTEGER NOT NULL,
        posflags VARCHAR(30),
        negflags VARCHAR(30)
);

CREATE TABLE target (
	id serial PRIMARY KEY,
	nick VARCHAR(20) NOT NULL,
	pid integer REFERENCES planet_canon(id) NOT NULL,
	tick smallint NOT NULL,
	uid integer REFERENCES user_list(id),
	UNIQUE(pid,tick)
);

CREATE TABLE intel (
	id serial PRIMARY KEY,
	pid integer NOT NULL UNIQUE REFERENCES planet_canon(id),
	nick VARCHAR(20),
	fakenick VARCHAR(20),
        defwhore BOOLEAN DEFAULT FALSE,
        gov VARCHAR (20),
        bg VARCHAR (25),
        covop BOOLEAN DEFAULT FALSE,
	reportchan VARCHAR(30),
	scanner BOOLEAN DEFAULT FALSE,
	distwhore BOOLEAN DEFAULT FALSE,
	comment VARCHAR(512),
	relay bool NOT NULL DEFAULT FALSE,
	nap bool NOT NULL DEFAULT FALSE,
	alliance_id integer REFERENCES alliance_canon(id)
);

CREATE TABLE epenis_cache (
    id SERIAL PRIMARY KEY,
    planet_id integer NOT NULL REFERENCES planet_canon(id),
    epenis integer NOT NULL,
    epenis_rank integer NOT NULL
);

CREATE TABLE ship (
	id SERIAL PRIMARY KEY,
	name VARCHAR(30) UNIQUE NOT NULL,
	class VARCHAR(10) NOT NULL CHECK(class in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship')),
	target_1 VARCHAR(10) NOT NULL CHECK(target_1 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct')),
	target_2 VARCHAR(10) CHECK(target_2 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct',NULL)),
	target_3 VARCHAR(10) CHECK(target_3 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct',NULL)),
	type VARCHAR(5) NOT NULL CHECK(type in ('Cloak','Norm','Pod','Struc','Emp','Steal')),
	init smallint NOT NULL,
	gun smallint NOT NULL,
	armor smallint NOT NULL,
	damage smallint,
	empres smallint NOT NULL,
	metal integer NOT NULL,
	crystal integer NOT NULL,
	eonium integer NOT NULL,
	race VARCHAR(10) NOT NULL CHECK(race in ('Terran','Cathaar','Xandathrii','Zikonian','Eitraides')),
	total_cost integer NOT NULL CHECK(total_cost = metal+crystal+eonium)
);

CREATE TABLE slogan (
	id serial PRIMARY KEY,
	slogan VARCHAR(512) NOT NULL
);

CREATE TABLE quote (
	id serial PRIMARY KEY,
	quote VARCHAR(512) NOT NULL
);


CREATE TABLE scan (
	id bigserial PRIMARY KEY,
	tick smallint NOT NULL,
	pid integer NOT NULL REFERENCES planet_canon(id),
	nick VARCHAR(15) NOT NULL,
	pnick VARCHAR(15) ,
	rand_id VARCHAR(20) NOT NULL,
        group_id VARCHAR(20),
	scantype VARCHAR(11) NOT NULL CHECK(scantype in ('unknown','planet','development','unit','news','jgp','fleet','au')),
	UNIQUE(rand_id,tick)
);


CREATE TABLE planet (
	id serial PRIMARY KEY,
	scan_id bigint NOT NULL REFERENCES scan(id),
	timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
	roid_metal smallint NOT NULL,
	roid_crystal smallint NOT NULL,
	roid_eonium smallint NOT NULL,
	res_metal integer NOT NULL,
	res_crystal integer NOT NULL,
	res_eonium integer NOT NULL,
	factory_usage_light VARCHAR(7) NOT NULL CHECK(factory_usage_light IN ('None','Low', 'Medium', 'High')),
	factory_usage_medium VARCHAR(7) NOT NULL CHECK(factory_usage_medium IN ('None','Low', 'Medium', 'High')),
	factory_usage_heavy VARCHAR(7) NOT NULL CHECK(factory_usage_heavy IN ('None','Low', 'Medium', 'High')),
	prod_res integer NOT NULL,
	agents integer NOT NULL,
	guards integer NOT NULL
);


CREATE TABLE development (
	id serial PRIMARY KEY,
	scan_id bigint NOT NULL REFERENCES scan(id),
	light_factory smallint NOT NULL,
	medium_factory smallint NOT NULL,
	heavy_factory smallint NOT NULL,
	wave_amplifier smallint NOT NULL,
	wave_distorter smallint NOT NULL,
	metal_refinery smallint NOT NULL,
	crystal_refinery smallint NOT NULL,
	eonium_refinery smallint NOT NULL,
	research_lab smallint NOT NULL,
	finance_centre smallint NOT NULL,
	security_centre smallint NOT NULL,
	travel smallint NOT NULL,
	infrastructure smallint NOT NULL,
	hulls smallint NOT NULL,
	waves smallint NOT NULL,
	core smallint NOT NULL,
	covert_op smallint NOT NULL,
	mining smallint NOT NULL
);

CREATE TABLE unit (
	id serial PRIMARY KEY,
	scan_id bigint NOT NULL REFERENCES scan(id),
	ship_id integer NOT NULL REFERENCES ship(id),
	amount integer NOT NULL
);

CREATE TABLE au (
    id serial PRIMARY KEY,
    scan_id bigint NOT NULL REFERENCES scan(id),
    ship_id integer NOT NULL REFERENCES ship(id),
    amount integer NOT NULL
);


CREATE TABLE fleet (
	id serial PRIMARY KEY,
	scan_id bigint REFERENCES scan(id),
	owner_id integer NOT NULL REFERENCES planet_canon(id),
	target integer NOT NULL REFERENCES planet_canon(id),
	fleet_size integer,
	fleet_name VARCHAR(24) NOT NULL,
	launch_tick smallint,
	landing_tick smallint NOT NULL,
	mission varchar(7) NOT NULL CHECK(mission in ('defend','attack','unknown','return')),
	UNIQUE(owner_id,target,fleet_size,fleet_name,landing_tick,mission)
);

CREATE TABLE fleet_content (
	id serial PRIMARY KEY,
	fleet_id integer NOT NULL REFERENCES fleet(id),
	ship_id integer NOT NULL REFERENCES ship(id),
	amount integer NOT NULL
);

CREATE TABLE defcall_status
(
  id serial PRIMARY KEY,
  status VARCHAR(15)
);

INSERT INTO defcall_status (id,status) VALUES (1, 'covered');
INSERT INTO defcall_status (id,status) VALUES (2, 'uncovered');
INSERT INTO defcall_status (id,status) VALUES (3, 'recheck');
INSERT INTO defcall_status (id,status) VALUES (4, 'impossible');
INSERT INTO defcall_status (id,status) VALUES (5, 'semicovered');
INSERT INTO defcall_status (id,status) VALUES (6, 'fake');
INSERT INTO defcall_status (id,status) VALUES (7, 'recall');
INSERT INTO defcall_status (id,status) VALUES (8, 'invalid');

CREATE TABLE defcalls
(
  id serial PRIMARY KEY,
  bcalc character varying(255),
  claimed_by varchar(15),
  status integer NOT NULL REFERENCES defcall_status(id),
  "comment" text,
  target integer NOT NULL REFERENCES planet_canon(id),
  landing_tick smallint NOT NULL
);

CREATE TABLE covop (
	id serial PRIMARY KEY,
	scan_id integer NOT NULL REFERENCES scan(id),
	covopper integer NOT NULL REFERENCES planet_canon(id),
	target integer NOT NULL REFERENCES planet_canon(id)
);


CREATE TABLE command_log (
    id serial PRIMARY KEY,
    command_prefix VARCHAR(1) NOT NULL,
    command VARCHAR(20) NOT NULL,
    command_parameters VARCHAR(512),
    nick VARCHAR(15) NOT NULL,
    pnick VARCHAR(15),
    username VARCHAR(20) NOT NULL,
    hostname VARCHAR(64) NOT NULL,
    target VARCHAR(150) NOT NULL,
    command_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE froglet_logs (
       id SERIAL PRIMARY KEY,
       acces_time timestamp NOT NULL DEFAULT NOW(),
       page_url VARCHAR(1023) NOT NULL,
       ip CIDR NOT NULL,
--       user_id integer NOT NULL REFERENCES user_list(id),
       pnick VARCHAR(15) NOT NULL
);

CREATE TABLE phone (
       id SERIAL PRIMARY KEY,
       user_id integer NOT NULL REFERENCES user_list(id),
       friend_id integer NOT NULL REFERENCES user_list(id)
);

CREATE TABLE sms_log (
       id SERIAL PRIMARY KEY,
       sender_id integer REFERENCES user_list(id),
       receiver_id integer REFERENCES user_list(id),
       phone VARCHAR(48),
       sms_text varchar(160) NOT NULL
);
       

CREATE SEQUENCE proposal_id_seq;

CREATE TABLE invite_proposal (
       id integer PRIMARY KEY NOT NULL DEFAULT nextval('proposal_id_seq'),
       active BOOLEAN NOT NULL DEFAULT TRUE,
       proposer_id integer NOT NULL REFERENCES user_list(id),
       person VARCHAR(15) NOT NULL,
       created TIMESTAMP NOT NULL DEFAULT now(),
       closed TIMESTAMP,
       padding integer DEFAULT 0,
       vote_result VARCHAR(7) CHECK(vote_result IN (NULL,'yes','no')),
       compensation integer,
       comment_text TEXT NOT NULL
);

CREATE TABLE kick_proposal (
       id integer PRIMARY KEY NOT NULL DEFAULT nextval('proposal_id_seq'),
       active BOOLEAN NOT NULL DEFAULT TRUE,
       proposer_id integer NOT NULL REFERENCES user_list(id),
       person_id integer NOT NULL REFERENCES user_list(id),
       created TIMESTAMP NOT NULL DEFAULT now(),
       closed TIMESTAMP,
       padding integer DEFAULT 0,
       vote_result VARCHAR(7) CHECK(vote_result IN (NULL,'yes','no')),
       compensation integer,
       comment_text TEXT NOT NULL
);

CREATE TABLE prop_vote (
       id SERIAL PRIMARY KEY,
       vote VARCHAR(7) NOT NULL CHECK(vote in ('yes', 'no', 'abstain')),
       carebears integer NOT NULL,
       prop_id integer NOT NULL,
       voter_id integer NOT NULL REFERENCES user_list(id)
);