-- CREATE DATABASE patools17 WITH ENCODING = 'LATIN1';
-- createlang plpgsql patest | CREATE LANGUAGE plpgqsl


CREATE TABLE updates (
id serial,
tick smallint UNIQUE,
planets smallint,
galaxies smallint,
alliances smallint,
userfeed smallint,
timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
PRIMARY KEY (id)
);

INSERT INTO updates VALUES (-1,-1,-1,-1,-1,-1);

CREATE TABLE planet_canon (
id serial,
uid varchar(12) UNIQUE,
active boolean NOT NULL DEFAULT TRUE,
PRIMARY KEY(id),
UNIQUE (uid)
);

CREATE TABLE planet_dump (
tick smallint REFERENCES updates (tick),
uid varchar(12),
x smallint,
y smallint,
z smallint,
planetname varchar(20) NOT NULL,
rulername varchar(30) NOT NULL,
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
FOREIGN KEY(uid) REFERENCES planet_canon (uid)
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
total_score bigint NOT NULL,
total_score_rank smallint NOT NULL,
total_score_avg int NOT NULL,
total_score_avg_rank smallint NOT NULL,
total_value bigint NOT NULL,
total_value_rank smallint NOT NULL,
total_value_avg int NOT NULL,
total_value_avg_rank smallint NOT NULL,
id integer NOT NULL REFERENCES alliance_canon(id),
PRIMARY KEY(tick, name)
);

CREATE TABLE userfeed_dump (
tick smallint,
type varchar(32) NOT NULL,
text varchar(255) NOT NULL,
PRIMARY KEY(tick, text)
);

CREATE INDEX planet_dump_tick_index ON planet_dump(tick);
CREATE INDEX planet_dump_id_index ON planet_dump(id);
CREATE INDEX planet_dump_rn_index ON planet_dump(rulername);
CREATE INDEX planet_dump_pn_index ON planet_dump(planetname);

CREATE INDEX galaxy_dump_tick_index ON galaxy_dump(tick);
CREATE INDEX galaxy_dump_id_index ON galaxy_dump(id);

CREATE INDEX alliance_dump_tick_index ON alliance_dump(tick);
CREATE INDEX alliance_dump_id_index ON alliance_dump(id);

CREATE INDEX userfeed_dump_tick_index ON userfeed_dump(tick);
CREATE INDEX userfeed_dump_text_index ON userfeed_dump(text);


CREATE TABLE anarchy (
id serial,
pid integer NOT NULL REFERENCES planet_canon(id),
start_tick smallint NOT NULL,
end_tick smallint NOT NULL,
PRIMARY KEY(id),
UNIQUE (pid, start_tick, end_tick),
FOREIGN KEY(pid) REFERENCES planet_canon(id)
);

CREATE INDEX anarchy_id_index ON anarchy(id);
CREATE INDEX anarchy_pid_index ON anarchy(pid);


CREATE TABLE user_list (
id SERIAL PRIMARY KEY,
pnick VARCHAR(15) NOT NULL,
alias_nick VARCHAR(15) UNIQUE CHECK (lower(alias_nick) NOT IN (lower(user_list.pnick))),
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

DROP FUNCTION IF EXISTS max_tick();
CREATE FUNCTION max_tick() RETURNS int AS $PROC$
BEGIN
RETURN MAX(tick) FROM updates;
END
$PROC$ LANGUAGE plpgsql;

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
target_1 VARCHAR(10) NOT NULL CHECK(target_1 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct','Rs')),
target_2 VARCHAR(10) CHECK(target_2 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct',NULL)),
target_3 VARCHAR(10) CHECK(target_3 in ('Fighter','Corvette','Frigate','Destroyer','Cruiser','Battleship','Roids','Struct',NULL)),
type VARCHAR(5) NOT NULL CHECK(type in ('Cloak','Norm','Pod','Struc','Emp','Steal','Res')),
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
scan_time TIMESTAMP WITHOUT TIME ZONE,
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
military_centre smallint NOT NULL,
security_centre smallint NOT NULL,
structure_defense smallint NOT NULL,
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
vote VARCHAR(7) NOT NULL CHECK(vote in ('yes', 'no', 'abstain', 'veto')),
carebears integer NOT NULL,
prop_id integer NOT NULL,
voter_id integer NOT NULL REFERENCES user_list(id)
);


-- Since the plpythonu language is unrestricted, functions must be created as
-- superuser. This is somewhat undesirable. Poop.

-- BEGIN HUGIN RELATED FUNCTIONS

DROP FUNCTION IF EXISTS trim_quotes(text,text);
CREATE FUNCTION trim_quotes(tmptab text,colname text) RETURNS void AS $PROC$
BEGIN
EXECUTE 'UPDATE '||tmptab||' SET '||colname||'=trim(''"'' FROM '||colname||')';
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS gen_planet_id();
CREATE FUNCTION gen_planet_id() RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE planet_canon SET active=FALSE WHERE ROW(uid) NOT IN (SELECT uid FROM ptmp);
-- insert new into canonical and update IDs
INSERT INTO planet_canon (uid) SELECT t1.uid FROM ptmp AS t1 WHERE ROW(t1.uid) NOT IN (SELECT uid FROM planet_canon);
-- insert IDs for existing
ALTER TABLE ptmp ADD COLUMN id integer DEFAULT -1;
UPDATE ptmp SET id=t1.id FROM planet_canon AS t1 WHERE ptmp.uid=t1.uid;
CREATE INDEX ptmp_id_index ON ptmp(id);
ANALYZE ptmp;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS gen_galaxy_id();
CREATE FUNCTION gen_galaxy_id() RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE galaxy_canon SET active=FALSE WHERE ROW(x,y) NOT IN (SELECT x,y FROM gtmp);
-- insert new into canonical and update IDs
INSERT INTO galaxy_canon (x,y) SELECT x,y FROM gtmp WHERE ROW(x,y) NOT IN (SELECT x,y FROM galaxy_canon);
-- insert IDs for existing
ALTER TABLE gtmp ADD COLUMN id integer DEFAULT -1;
UPDATE gtmp SET id=t1.id FROM galaxy_canon AS t1 WHERE gtmp.x=t1.x AND gtmp.y=t1.y;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS gen_alliance_id();
CREATE FUNCTION gen_alliance_id() RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE alliance_canon SET active=FALSE WHERE ROW(name) NOT IN (SELECT name FROM atmp);
-- insert new into canonical and update IDs
INSERT INTO alliance_canon (name) SELECT name FROM atmp WHERE ROW(name) NOT IN (SELECT name FROM alliance_canon);
-- insert IDs for existing
ALTER TABLE atmp ADD COLUMN id integer DEFAULT -1;

UPDATE atmp SET id=t1.id FROM alliance_canon AS t1 WHERE atmp.name=t1.name;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS add_rank(text,text);
CREATE FUNCTION add_rank(tmptab text,colname text) RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
EXECUTE 'ALTER TABLE '||quote_ident(tmptab)||' ADD COLUMN '||quote_ident(colname)||'_rank smallint DEFAULT -1';
FOR r IN EXECUTE 'SELECT id FROM '||quote_ident(tmptab)||' ORDER BY '||quote_ident(colname)||' DESC' LOOP
rank := rank + 1;
EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(colname)||'_rank='||rank||' WHERE id='||r.id;
END LOOP;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS add_average(text,text,text,text);
CREATE FUNCTION add_average(tmptab text,value_colname text,quantity_colname text,coltype text) RETURNS void AS $PROC$
BEGIN
EXECUTE 'ALTER TABLE '||quote_ident(tmptab)||' ADD COLUMN '||quote_ident(value_colname)||'_avg '||coltype||' DEFAULT -1';
EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(value_colname)||'_avg='||quote_ident(value_colname)||'::bigint/'||quote_ident(quantity_colname)||'::bigint';
END
$PROC$ LANGUAGE plpgsql;

-- PLANET SPECIFIC RANK FUNCTIONS FOR PERFORMANCE

DROP FUNCTION IF EXISTS add_rank_planet_size();
CREATE FUNCTION add_rank_planet_size() RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
ALTER TABLE ptmp ADD COLUMN size_rank smallint DEFAULT -1;
FOR r IN SELECT id FROM ptmp ORDER BY size DESC LOOP
rank := rank + 1;
UPDATE ptmp SET size_rank=rank WHERE id=r.id;
END LOOP;
END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS add_rank_planet_score();
CREATE FUNCTION add_rank_planet_score() RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
ALTER TABLE ptmp ADD COLUMN score_rank smallint DEFAULT -1;
FOR r IN SELECT id FROM ptmp ORDER BY score DESC LOOP
rank := rank + 1;
UPDATE ptmp SET score_rank=rank WHERE id=r.id;
END LOOP;
END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS add_rank_planet_value();
CREATE FUNCTION add_rank_planet_value() RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
ALTER TABLE ptmp ADD COLUMN value_rank smallint DEFAULT -1;
FOR r IN SELECT id FROM ptmp ORDER BY value DESC LOOP
rank := rank + 1;
UPDATE ptmp SET value_rank=rank WHERE id=r.id;
END LOOP;
END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS add_rank_planet_xp();
CREATE FUNCTION add_rank_planet_xp() RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
ALTER TABLE ptmp ADD COLUMN xp_rank smallint DEFAULT -1;
FOR r IN SELECT id FROM ptmp ORDER BY xp DESC LOOP
rank := rank + 1;
UPDATE ptmp SET xp_rank=rank WHERE id=r.id;
END LOOP;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS add_planet_idle_ticks(smallint);
CREATE FUNCTION add_planet_idle_ticks(curtick smallint) RETURNS void AS $PROC$
BEGIN
ALTER TABLE ptmp ADD COLUMN idle smallint DEFAULT 0;
ALTER TABLE ptmp ADD COLUMN vdiff integer DEFAULT 0;

UPDATE ptmp SET vdiff = ptmp.value - t2.value
FROM planet_dump AS t2
WHERE ptmp.id=t2.id AND t2.tick=curtick-1;

UPDATE ptmp SET idle = t2.idle + 1
FROM planet_dump AS t2
WHERE ptmp.id=t2.id AND t2.tick=curtick-1 AND ptmp.vdiff >= t2.vdiff - 1 AND ptmp.vdiff <= t2.vdiff + 1 AND ptmp.xp - t2.xp = 0;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS store_planets(smallint);
CREATE FUNCTION store_planets(curtick smallint) RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
--remove quotes from names added by the dumpfile generator

PERFORM trim_quotes('ptmp','rulername');
PERFORM trim_quotes('ptmp','planetname');
--generate IDs, insert missing into canonical, deactive missing planets

PERFORM gen_planet_id();

--generate ranks, this will add the appropriate columns to the temp table

PERFORM add_rank_planet_size();
PERFORM add_rank_planet_score();
PERFORM add_rank_planet_value();
PERFORM add_rank_planet_xp();
PERFORM add_planet_idle_ticks(curtick);

--transfer temporary data into permanent dump
INSERT INTO planet_dump (tick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id)
SELECT curtick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id FROM ptmp;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS store_galaxies(smallint);
CREATE FUNCTION store_galaxies(curtick smallint) RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('gtmp','name');
--generate IDs, insert missing into canonical, deactive missing galaxies
PERFORM gen_galaxy_id();
--generate ranks, this will add the appropriate columns to the temp table (Should we generate averages here? Probably not, hassle (requires grabbing planet info for count) and not worth much)

PERFORM add_rank('gtmp','size');
PERFORM add_rank('gtmp','score');
PERFORM add_rank('gtmp','value');
PERFORM add_rank('gtmp','xp');

--transfer tmp to dump
INSERT INTO galaxy_dump (tick,x,y,name,size,score,value,xp,size_rank,score_rank,value_rank,xp_rank,id)
SELECT curtick,x,y,name,size,COALESCE(score,0),value,xp,size_rank,score_rank,value_rank,xp_rank,id FROM gtmp;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS store_alliances(smallint);
CREATE FUNCTION store_alliances(curtick smallint) RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('atmp','name');
--generate IDs, insert missing into canonical, deactive missing alliances
PERFORM gen_alliance_id();

--adding of missing columns done automatically in each add_ sproc
--generate averages (should we limit members to 70 since that's all that will be counted? Probably, but let's wait for PAteam to finish deciding)
PERFORM add_average('atmp','size','members','smallint');
PERFORM add_average('atmp','score','members','integer');
PERFORM add_average('atmp','total_score','members','integer');
PERFORM add_average('atmp','total_value','members','integer');
--generate ranks
PERFORM add_rank('atmp','size');
PERFORM add_rank('atmp','members');
PERFORM add_rank('atmp','size_avg');
PERFORM add_rank('atmp','score_avg');

PERFORM add_rank('atmp','total_score');
PERFORM add_rank('atmp','total_value');
PERFORM add_rank('atmp','total_score_avg');
PERFORM add_rank('atmp','total_value_avg');

--transfer tmp to dump
INSERT INTO alliance_dump (tick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,total_score,total_score_rank,total_score_avg,total_score_avg_rank,total_value,total_value_rank,total_value_avg,total_value_avg_rank,id)
SELECT curtick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,total_score,total_score_rank,total_score_avg,total_score_avg_rank,total_value,total_value_rank,total_value_avg,total_value_avg_rank,id FROM atmp;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS store_userfeed();
CREATE FUNCTION store_userfeed() RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('utmp','type');
PERFORM trim_quotes('utmp','text');

-- TRUNCATE queries can be replaced by ON CONFLICT DO NOTHING in postgres 9.5
-- and later.

--transfer tmp to dump
TRUNCATE userfeed_dump;
INSERT INTO userfeed_dump (tick,type,text)
SELECT tick,type,text FROM utmp
--ON CONFLICT DO NOTHING;

--extract anarchy data
ALTER TABLE utmp ADD COLUMN x smallint;
UPDATE utmp SET x=substring(text from '(\d+):\d+:\d+')::smallint;
ALTER TABLE utmp ADD COLUMN y smallint;
UPDATE utmp SET y=substring(text from '\d+:(\d+):\d+')::smallint;
ALTER TABLE utmp ADD COLUMN z smallint;
UPDATE utmp SET z=substring(text from '\d+:\d+:(\d+)')::smallint;
ALTER TABLE utmp ADD COLUMN anarchy_end_tick smallint;
UPDATE utmp SET anarchy_end_tick=substring(text from 'until tick (\d+)')::smallint;
ALTER TABLE utmp add COLUMN pid integer DEFAULT NULL;
UPDATE utmp SET pid=p.id FROM planet_dump AS p WHERE utmp.x = p.x AND utmp.y = p.y AND utmp.z = p.z AND utmp.tick = p.tick;

--transfer anarchy data, exclude exit anarchy entries
--
TRUNCATE anarchy;
INSERT INTO anarchy (start_tick, end_tick, pid)
SELECT tick, anarchy_end_tick, pid FROM utmp WHERE anarchy_end_tick IS NOT NULL AND pid IS NOT NULL
--ON CONFLICT DO NOTHING;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS store_update(smallint,text,text,text);
DROP FUNCTION IF EXISTS store_update(smallint,text,text,text,text);
CREATE FUNCTION store_update(curtick smallint,ptable text,gtable text,atable text,utable text) RETURNS void AS $PROC$
BEGIN
INSERT INTO updates (tick,planets,galaxies,alliances,userfeed) VALUES (curtick,(SELECT COUNT(*) FROM quote_ident(ptable)),(SELECT COUNT(*) FROM quote_ident(gtable)),(SELECT COUNT(*) FROM quote_ident(atable)),(SELECT COUNT(*) FROM quote_ident(utable)));
END
$PROC$ LANGUAGE plpgsql;

-- END HUGIN RELATED FUNCTIONS

-- Function: defcall_update()

DROP FUNCTION IF EXISTS defcall_update();

CREATE OR REPLACE FUNCTION defcall_update()
RETURNS "trigger" AS
$BODY$
DECLARE
is_friendly boolean;
defcall_id integer;
BEGIN

is_friendly := false;
defcall_id = 0;

SELECT INTO is_friendly COUNT(*)
FROM alliance_canon a, intel
WHERE intel.alliance_id = a.id
AND a.name ILIKE 'ascendancy'
AND NEW.mission ILIKE 'attack'
AND intel.pid = NEW.target;

IF is_friendly THEN
SELECT INTO defcall_id id
FROM defcalls WHERE target=NEW.target
AND landing_tick = NEW.landing_TICK;

IF defcall_id > 0 THEN
UPDATE defcalls SET status = 3 WHERE id = defcall_id;
ELSE
INSERT INTO defcalls (status, target, landing_tick) VALUES(2, NEW.target, NEW.landing_tick);
END IF;
END IF;

RETURN NEW;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE;
ALTER FUNCTION defcall_update() OWNER TO munin;

CREATE TRIGGER fleet_updates_defcalls
BEFORE INSERT OR UPDATE
ON fleet
FOR EACH ROW
EXECUTE PROCEDURE defcall_update();

-- BEGIN MUNIN RELATED FUNCTIONS

DROP FUNCTION IF EXISTS gal_value(smallint,smallint);
CREATE FUNCTION gal_value(gal_x smallint, gal_y smallint) RETURNS int AS $PROC$
BEGIN
RETURN sum(value) FROM planet_dump
WHERE tick=(SELECT max_tick()) AND x=gal_x AND y=gal_y
GROUP BY x,y;
END
$PROC$ LANGUAGE plpgsql;

-- END MUNIN RELATED FUNCTIONS
