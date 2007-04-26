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
     name varchar(16) UNIQUE,
     active boolean NOT NULL DEFAULT TRUE,
     PRIMARY KEY(id)
    );

    CREATE TABLE alliance_dump (
     tick smallint REFERENCES updates (tick),
     name varchar(16) NOT NULL REFERENCES alliance_canon (name),
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

    CREATE INDEX galaxy_dump_tick_index ON galaxy_dump(tick);

    CREATE INDEX galaxy_dump_id_index ON galaxy_dump(id);

    CREATE INDEX alliance_dump_tick_index ON alliance_dump(tick);

    CREATE INDEX alliance_dump_id_index ON alliance_dump(id);



    CREATE TABLE user_list (
        id SERIAL PRIMARY KEY,
        pnick VARCHAR(15) NOT NULL UNIQUE,
        sponsor VARCHAR(15),
        passwd CHAR(30),
        userlevel INTEGER NOT NULL,
	posflags VARCHAR(30),
	negflags VARCHAR(30),
	planet_id integer REFERENCES planet_canon(id) ON DELETE CASCADE,
	stay BOOLEAN DEFAULT FALSE,
	invites smallint NOT NULL DEFAULT 0 CHECK (invites >= 0),
	quit smallint NOT NULL DEFAULT 0
);

INSERT INTO user_list (pnick,sponsor,userlevel) VALUES ('jester','Munin',1000);

CREATE TABLE kickvote (
	id SERIAL PRIMARY KEY,
	voter integer REFERENCES user_list(id) ON DELETE CASCADE,
	moron integer REFERENCES user_list(id) ON DELETE CASCADE,
	UNIQUE(voter,moron)
);

CREATE TABLE channel_list (
	id SERIAL PRIMARY KEY,
	chan VARCHAR(150) NOT NULL UNIQUE,
        userlevel INTEGER NOT NULL,
	maxlevel INTEGER NOT NULL,
        posflags VARCHAR(30),
        negflags VARCHAR(30)
);

--DROP TRIGGER chan_max_level ON channel_list;
--DROP FUNCTION chan_max_level();
/*
IT WOULD BE NICE IF THIS WORKED, REALLY IT WOULD 
CREATE FUNCTION chan_max_level() RETURNS trigger AS $PROC$
BEGIN
	NEW.maxlevel := NEW.userlevel;
	RETURN NEW;
END
$PROC$ LANGUAGE plpgsql;

CREATE TRIGGER chan_max_level BEFORE INSERT ON channel_list FOR EACH ROW EXECUTE PROCEDURE chan_max_level();*/

CREATE TABLE sponsor (
	id SERIAL PRIMARY KEY,
	sponsor_id integer REFERENCES user_list(id) ON DELETE CASCADE,
	pnick VARCHAR(15) NOT NULL UNIQUE,--CHECK (pnick NOT IN (SELECT pnick FROM user_list)),
	comment VARCHAR(512),
	timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

/*
CREATE FUNCTION recruit_not_member() RETURNS trigger AS $PROC$
BEGIN
	IF NEW.pnick IN (SELECT pnick FROM user_list) THEN
		RAISE EXCEPTION '% is already a member', NEW.pnick;
	END IF;
        RETURN NEW;
END
$PROC$ LANGUAGE plpgsql;

CREATE TRIGGER recruit_not_member BEFORE INSERT ON sponsor FOR EACH ROW EXECUTE PROCEDURE recruit_not_member();
*/


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
	alliance VARCHAR(20),
	reportchan VARCHAR(30),
	hostile_count smallint,
	scanner BOOLEAN DEFAULT FALSE,
	distwhore BOOLEAN DEFAULT FALSE,
	comment VARCHAR(512)	
);

CREATE FUNCTION intel_update_nulls() RETURNS trigger AS $PROC$
BEGIN
IF NEW.nick = '?' THEN
	NEW.nick=NULL;
END IF;
IF NEW.fakenick = '?' THEN
	NEW.fakenick=NULL;
END IF;
IF NEW.alliance = '?' THEN
        NEW.alliance=NULL;
END IF;
IF NEW.reportchan = '?' THEN
        NEW.reportchan=NULL;
END IF;
IF NEW.comment = '?' THEN
        NEW.comment=NULL;
END IF;
RETURN NEW;
END
$PROC$ LANGUAGE plpgsql;


CREATE TRIGGER intel_update_nulls BEFORE UPDATE ON intel FOR EACH ROW EXECUTE PROCEDURE intel_update_nulls();
CREATE TRIGGER intel_insert_nulls BEFORE INSERT ON intel FOR EACH ROW EXECUTE PROCEDURE intel_update_nulls();

CREATE TABLE ship (
	id SERIAL PRIMARY KEY,
	name VARCHAR(30) UNIQUE NOT NULL,
	class VARCHAR(10) NOT NULL CHECK(class in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship')),
	target VARCHAR(10) NOT NULL CHECK(target in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct')),
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

CREATE TABLE tag (
	id serial PRIMARY KEY,
	pid integer NOT NULL REFERENCES planet_canon(id),
	tick smallint NOT NULL REFERENCES updates(tick),
	aid integer NOT NULL REFERENCES alliance_canon(id),
	quality smallint NOT NULL DEFAULT 0 CHECK(quality > -1 AND quality < 101),
	UNIQUE(pid,tick)
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
	id serial PRIMARY KEY,
	tick smallint NOT NULL,
	pid integer NOT NULL REFERENCES planet_canon(id),
	nick VARCHAR(15) NOT NULL,
	pnick VARCHAR(15) ,
	rand_id integer NOT NULL,
	scantype VARCHAR(10) NOT NULL CHECK(scantype in ('unknown','planet','structure','technology','unit','news','jgp','fleet','au')),
	UNIQUE(rand_id,tick)
);

--CREATE INDEX scan_pid_index ON scan(pid);

--CREATE INDEX  ON alliance_dump(id);


CREATE TABLE planet (
	id serial PRIMARY KEY,
	scan_id integer NOT NULL REFERENCES scan(id),
	timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
	roid_metal smallint NOT NULL,
	roid_crystal smallint NOT NULL,
	roid_eonium smallint NOT NULL,
	res_metal integer NOT NULL,
	res_crystal integer NOT NULL,
	res_eonium integer NOT NULL
);

CREATE TABLE structure (
	id serial PRIMARY KEY,
	scan_id integer NOT NULL REFERENCES scan(id),
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
	security_centre smallint NOT NULL
);

CREATE TABLE technology (
	id serial PRIMARY KEY,
	scan_id integer NOT NULL REFERENCES scan(id),
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
	scan_id integer NOT NULL REFERENCES scan(id),
	ship_id integer NOT NULL REFERENCES ship(id),
	amount integer NOT NULL
);

CREATE TABLE au (
    id serial PRIMARY KEY,
    scan_id integer NOT NULL REFERENCES scan(id),
    ship_id integer NOT NULL REFERENCES ship(id),
    amount integer NOT NULL
);


/*CREATE VIEW unit_ranges AS --broken
	SELECT t2.pid AS pid,t3.name,max(amount::float)/1.2 AS min_amount,min(t1.amount::float)*.8 AS max_amount
	FROM unit AS t1
	INNER JOIN ship AS t3
	ON t1.ship_id=t3.id
	INNER JOIN scan AS t2
	ON t1.scan_id=t2.id
	GROUP BY t2.tick,t2.pid,t3.name
	HAVING t2.tick=max(t2.tick)
;*/

CREATE TABLE fleet (
	id serial PRIMARY KEY,
	scan_id integer REFERENCES scan(id),
	owner integer NOT NULL REFERENCES planet_canon(id),
	target integer NOT NULL REFERENCES planet_canon(id),
	fleet_size integer, 
	fleet_name VARCHAR(24) NOT NULL,
	launch_tick smallint, 
	landing_tick smallint NOT NULL,
	mission varchar(7) NOT NULL CHECK(mission in ('defend','attack','unknown','return')),
	UNIQUE(owner,target,fleet_size,fleet_name,landing_tick,mission)
);

CREATE TABLE fleet_content (
	id serial PRIMARY KEY,
	fleet_id integer NOT NULL REFERENCES fleet(id),
	ship_id integer NOT NULL REFERENCES ship(id),
	amount integer NOT NULL
);


CREATE TABLE covop (
	id serial PRIMARY KEY,
	scan_id integer NOT NULL REFERENCES scan(id),
	covopper integer NOT NULL REFERENCES planet_canon(id),
	target integer NOT NULL REFERENCES planet_canon(id)
);
