CREATE FUNCTION max_round() RETURNS smallint AS $PROC$
BEGIN
RETURN MAX(round) FROM updates;
END
$PROC$ LANGUAGE plpgsql;

-- These foreign keys rely on the primary key of updates. We'll re-add their
-- replacements later.
ALTER TABLE planet_dump DROP CONSTRAINT planet_dump_tick_fkey;
ALTER TABLE galaxy_dump DROP CONSTRAINT galaxy_dump_tick_fkey;
ALTER TABLE alliance_dump DROP CONSTRAINT alliance_dump_tick_fkey;
ALTER TABLE fleet_log DROP CONSTRAINT fleet_log_tick_fkey;

ALTER TABLE updates DROP CONSTRAINT updates_tick_key;
ALTER TABLE updates ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE updates ALTER COLUMN round DROP DEFAULT;
UPDATE updates SET round=-1 WHERE tick=-1;
ALTER TABLE updates ADD CONSTRAINT updates_round_tick_key UNIQUE (round, tick);

-- Another foreign key to replace.
ALTER TABLE planet_dump DROP CONSTRAINT planet_dump_uid_fkey;

ALTER TABLE planet_canon DROP CONSTRAINT planet_canon_uid_key;
ALTER TABLE planet_canon ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE planet_canon ALTER COLUMN round DROP DEFAULT;
ALTER TABLE planet_canon ADD CONSTRAINT planet_canon_uid_round_key UNIQUE (uid, round);

ALTER TABLE planet_dump DROP CONSTRAINT planet_dump_pkey;
ALTER TABLE planet_dump ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE planet_dump ALTER COLUMN round DROP DEFAULT;
ALTER TABLE planet_dump ADD CONSTRAINT planet_dump_uid_fkey FOREIGN KEY (uid, round) REFERENCES planet_canon (uid, round);
ALTER TABLE planet_dump ADD CONSTRAINT planet_dump_tick_fkey FOREIGN KEY (tick, round) REFERENCES updates (tick, round);
ALTER TABLE planet_dump ADD CONSTRAINT planet_dump_pkey PRIMARY KEY (round, tick, x, y, z);
DROP INDEX planet_dump_tick_index;

-- More dependent keys!
ALTER TABLE galaxy_dump DROP CONSTRAINT galaxy_dump_x_fkey;

ALTER TABLE galaxy_canon DROP CONSTRAINT galaxy_canon_x_y_key;
ALTER TABLE galaxy_canon ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE galaxy_canon ALTER COLUMN round DROP DEFAULT;
ALTER TABLE galaxy_canon ADD CONSTRAINT galaxy_canon_round_x_y_key UNIQUE(round,x,y);

ALTER TABLE galaxy_dump DROP CONSTRAINT galaxy_dump_pkey;
ALTER TABLE galaxy_dump ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE galaxy_dump ALTER COLUMN round DROP DEFAULT;
ALTER TABLE galaxy_dump ADD CONSTRAINT galaxy_dump_round_fkey FOREIGN KEY (round, x, y) REFERENCES galaxy_canon (round, x, y);
ALTER TABLE galaxy_dump ADD CONSTRAINT galaxy_dump_round_fkey1 FOREIGN KEY (round, tick) REFERENCES updates (round, tick);
ALTER TABLE galaxy_dump ADD CONSTRAINT galaxy_dump_pkey PRIMARY KEY (round, tick, x, y);
DROP INDEX galaxy_dump_tick_index;
DROP INDEX galaxy_dump_id_index;

-- And yet another foreign key.
ALTER TABLE alliance_dump DROP CONSTRAINT alliance_dump_name_fkey;

ALTER TABLE alliance_canon DROP CONSTRAINT alliance_canon_name_key;
ALTER TABLE alliance_canon ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE alliance_canon ALTER COLUMN round DROP DEFAULT;
ALTER TABLE alliance_canon ADD CONSTRAINT alliance_canon_round_name_key UNIQUE (round, name);

ALTER TABLE alliance_dump DROP CONSTRAINT alliance_dump_pkey;
ALTER TABLE alliance_dump ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE alliance_dump ALTER COLUMN round DROP DEFAULT;
ALTER TABLE alliance_dump ADD CONSTRAINT alliance_dump_name_fkey FOREIGN KEY (name, round) REFERENCES alliance_canon (name, round);
ALTER TABLE alliance_dump ADD CONSTRAINT alliance_dump_round_fkey FOREIGN KEY (round, tick) REFERENCES updates (round, tick);
ALTER TABLE alliance_dump ADD CONSTRAINT alliance_dump_pkey PRIMARY KEY (round, tick, name);
DROP INDEX alliance_dump_tick_index;
DROP INDEX alliance_dump_id_index;

ALTER TABLE userfeed_dump DROP CONSTRAINT userfeed_dump_pkey;
ALTER TABLE userfeed_dump ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE userfeed_dump ALTER COLUMN round DROP DEFAULT;
ALTER TABLE userfeed_dump ADD CONSTRAINT userfeed_dump_pkey PRIMARY KEY (round, tick, text);

ALTER TABLE alliance_relation ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE alliance_relation ALTER COLUMN round DROP DEFAULT;
CREATE INDEX alliance_relation_round_index ON alliance_relation(round);

ALTER TABLE anarchy ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE anarchy ALTER COLUMN round DROP DEFAULT;
CREATE INDEX anarchy_round_index ON anarchy(round);

CREATE TABLE round_user_pref (
    id serial,
    user_id integer REFERENCES user_list(id),
    round smallint NOT NULL,
    planet_id integer REFERENCES planet_canon(id) ON DELETE CASCADE,
    stay boolean DEFAULT FALSE,
    fleetcount integer NOT NULL DEFAULT 0,
    fleetcomment varchar(512) NOT NULL DEFAULT '',
    fleetupdated integer NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE (user_id, round)
);
INSERT INTO round_user_pref (user_id, round, planet_id, stay, fleetcount, fleetcomment, fleetupdated)
SELECT u.id, 71, u.planet_id, u.stay, u.fleetcount, u.fleetcomment, u.fleetupdated
FROM user_list AS u;

ALTER TABLE user_list DROP COLUMN planet_id;
ALTER TABLE user_list DROP COLUMN stay;
ALTER TABLE user_list DROP COLUMN fleetcount;
ALTER TABLE user_list DROP COLUMN fleetcomment;
ALTER TABLE user_list DROP COLUMN fleetupdated;

ALTER TABLE user_fleet ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE user_fleet ALTER COLUMN round DROP DEFAULT;

CREATE FUNCTION max_tick(r smallint) RETURNS smallint AS $PROC$
BEGIN
    RETURN MAX(tick) FROM updates WHERE r = round;
END
$PROC$ LANGUAGE plpgsql;

ALTER TABLE fleet_log ALTER COLUMN tick SET DEFAULT max_tick(max_round());
ALTER TABLE fleet_log ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE fleet_log ALTER COLUMN round DROP DEFAULT;
ALTER TABLE fleet_log ADD CONSTRAINT user_fleet_round_fkey FOREIGN KEY (round, tick) REFERENCES updates (round, tick);

DROP FUNCTION max_tick();

ALTER TABLE target ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE target ALTER COLUMN round DROP DEFAULT;
CREATE INDEX target_round_tick_index ON target (round, tick);

ALTER TABLE intel ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE intel ALTER COLUMN round DROP DEFAULT;

ALTER TABLE ship DROP CONSTRAINT ship_name_key;
ALTER TABLE ship ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE ship ALTER COLUMN round DROP DEFAULT;
ALTER TABLE ship ADD CONSTRAINT user_fleet_round_key UNIQUE (round, name);

ALTER TABLE scan DROP CONSTRAINT scan_rand_id_tick_key;
ALTER TABLE scan ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE scan ALTER COLUMN round DROP DEFAULT;
ALTER TABLE scan ADD CONSTRAINT scan_rand_id_tick_round_key UNIQUE (rand_id, tick, round);

ALTER TABLE fleet DROP CONSTRAINT fleet_owner_id_target_fleet_size_fleet_name_landing_tick_mi_key;
ALTER TABLE fleet ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE fleet ALTER COLUMN round DROP DEFAULT;
ALTER TABLE fleet ADD CONSTRAINT fleet_owner_id_target_fleet_size_fleet_name_round_landing_t_key UNIQUE (owner_id, target, fleet_size, fleet_name, round, landing_tick, mission);

ALTER TABLE fleet_content ADD COLUMN round smallint NOT NULL DEFAULT 71;
ALTER TABLE fleet_content ALTER COLUMN round DROP DEFAULT;


DROP FUNCTION gen_planet_id();
CREATE FUNCTION gen_planet_id(curround smallint) RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE planet_canon SET active=FALSE WHERE round = curround AND ROW(uid) NOT IN (SELECT uid FROM ptmp);
-- insert new into canonical and update IDs
INSERT INTO planet_canon (round,uid) SELECT curround, t1.uid FROM ptmp AS t1 WHERE ROW(t1.uid) NOT IN (SELECT uid FROM planet_canon WHERE round = curround);
-- insert IDs for existing
ALTER TABLE ptmp ADD COLUMN id integer DEFAULT -1;
UPDATE ptmp SET id=t1.id FROM planet_canon AS t1 WHERE ptmp.uid=t1.uid AND t1.round=curround;
CREATE INDEX ptmp_id_index ON ptmp(id);
ANALYZE ptmp;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION gen_galaxy_id();
CREATE FUNCTION gen_galaxy_id(curround smallint) RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE galaxy_canon SET active=FALSE WHERE round = curround AND ROW(x,y) NOT IN (SELECT x,y FROM gtmp);
-- insert new into canonical and update IDs
INSERT INTO galaxy_canon (round,x,y) SELECT curround,x,y FROM gtmp WHERE ROW(x,y) NOT IN (SELECT x,y FROM galaxy_canon WHERE round = curround);
-- insert IDs for existing
ALTER TABLE gtmp ADD COLUMN id integer DEFAULT -1;
UPDATE gtmp SET id=t1.id FROM galaxy_canon AS t1 WHERE gtmp.x=t1.x AND gtmp.y=t1.y AND t1.round=curround;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION gen_alliance_id();
CREATE FUNCTION gen_alliance_id(curround smallint) RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE alliance_canon SET active=FALSE WHERE round = curround AND ROW(name) NOT IN (SELECT name FROM atmp);
-- insert new into canonical and update IDs
INSERT INTO alliance_canon (round,name) SELECT curround,name FROM atmp WHERE ROW(name) NOT IN (SELECT name FROM alliance_canon WHERE round = curround);
-- insert IDs for existing
ALTER TABLE atmp ADD COLUMN id integer DEFAULT -1;
UPDATE atmp SET id=t1.id FROM alliance_canon AS t1 WHERE atmp.name=t1.name AND t1.round = curround;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_planets(smallint);
CREATE FUNCTION store_planets(curround smallint, curtick smallint) RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
--remove quotes from names added by the dumpfile generator

PERFORM trim_quotes('ptmp','rulername');
PERFORM trim_quotes('ptmp','planetname');
--generate IDs, insert missing into canonical, deactive missing planets

PERFORM gen_planet_id(curround);

--generate ranks, this will add the appropriate columns to the temp table

PERFORM add_rank_planet_size();
PERFORM add_rank_planet_score();
PERFORM add_rank_planet_value();
PERFORM add_rank_planet_xp();
PERFORM add_planet_idle_ticks(curtick);

--transfer temporary data into permanent dump
INSERT INTO planet_dump (round,tick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id)
SELECT curround,curtick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id FROM ptmp;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_galaxies(smallint);
CREATE FUNCTION store_galaxies(curround smallint, curtick smallint) RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('gtmp','name');
--generate IDs, insert missing into canonical, deactive missing galaxies
PERFORM gen_galaxy_id(curround);
--generate ranks, this will add the appropriate columns to the temp table (Should we generate averages here? Probably not, hassle (requires grabbing planet info for count) and not worth much)

PERFORM add_rank('gtmp','size');
PERFORM add_rank('gtmp','score');
PERFORM add_rank('gtmp','value');
PERFORM add_rank('gtmp','xp');

--transfer tmp to dump
INSERT INTO galaxy_dump (round,tick,x,y,name,size,score,value,xp,size_rank,score_rank,value_rank,xp_rank,id)
SELECT curround,curtick,x,y,name,size,COALESCE(score,0),value,xp,size_rank,score_rank,value_rank,xp_rank,id FROM gtmp;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_alliances(smallint);
CREATE FUNCTION store_alliances(curround smallint, curtick smallint) RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('atmp','name');
--generate IDs, insert missing into canonical, deactive missing alliances
PERFORM gen_alliance_id(curround);

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
INSERT INTO alliance_dump (round,tick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,total_score,total_score_rank,total_score_avg,total_score_avg_rank,total_value,total_value_rank,total_value_avg,total_value_avg_rank,id)
SELECT curround,curtick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,total_score,total_score_rank,total_score_avg,total_score_avg_rank,total_value,total_value_rank,total_value_avg,total_value_avg_rank,id FROM atmp;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION analyze_naps();
CREATE FUNCTION analyze_naps(curround smallint) RETURNS void AS $PROC$
BEGIN
-- NAP start.
UPDATE utmp as main
SET relation_type='NAP',
relation_end_tick = 32767,
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '(.*) and .* have confirmed they have formed a non-aggression pact')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '.* and (.*) have confirmed they have formed a non-aggression pact')
              AND tick = main.tick
              AND round = curround)
WHERE main.text ILIKE '% and % have confirmed they have formed a non-aggression pact%';

-- NAP end.
UPDATE utmp as main SET
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '(.*) has decided to end its NAP with .*')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '.* has decided to end its NAP with (.*)\.')
              AND tick = main.tick
              AND round = curround)
WHERE main.text ILIKE '% has decided to end its NAP with %';

-- NAP end tick
UPDATE utmp AS main
SET relation_end_tick = other.tick
FROM utmp AS other
WHERE ((other.alliance1_id = main.alliance1_id AND other.alliance2_id = main.alliance2_id)
       OR
       (other.alliance1_id = main.alliance2_id AND other.alliance2_id = main.alliance1_id))
AND main.relation_type = 'NAP'
AND other.tick > main.tick
AND other.text ILIKE '% has decided to end its NAP with %';

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION analyze_alliances();
CREATE FUNCTION analyze_alliances(curround smallint) RETURNS void AS $PROC$
BEGIN

-- Ally start.
UPDATE utmp as main
SET relation_type='Ally',
relation_end_tick = 32767,
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '(.*) and .* have confirmed they are allied')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '.* and (.*) have confirmed they are allied')
              AND tick = main.tick
              AND round = curround)
WHERE main.text ILIKE '% and % have confirmed they are allied%';

-- Ally end.
UPDATE utmp as main SET
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '(.*) has decided to end its alliance with .*')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(main.text from '.* has decided to end its alliance with (.*)\.')
              AND tick = main.tick
              AND round = curround)
WHERE main.text ILIKE '% has decided to end its alliance with %';

-- Ally end tick
UPDATE utmp AS main
SET relation_end_tick = other.tick
FROM utmp AS other
WHERE ((other.alliance1_id = main.alliance1_id AND other.alliance2_id = main.alliance2_id)
       OR
       (other.alliance1_id = main.alliance2_id AND other.alliance2_id = main.alliance1_id))
AND main.relation_type = 'Ally'
AND other.tick > main.tick
AND other.text ILIKE '% has decided to end its alliance with %';

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION analyze_wars();
CREATE FUNCTION analyze_wars(curround smallint) RETURNS void AS $PROC$
BEGIN

-- War start and default end tick.
UPDATE utmp AS main SET relation_type='War',
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '(.*) has declared war on .*')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '.* has declared war on (.*) !')
              AND tick = main.tick
              AND round = curround),
relation_end_tick=(tick+48) -- Wars have a fixed length of 48 ticks.
WHERE text ILIKE '% has declared war on %';

-- War end.
UPDATE utmp AS main SET
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '(.*)''s war with .* has expired.')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '.*''s war with (.*) has expired.')
              AND tick = main.tick
              AND round = curround)
WHERE text ILIKE '%''s war with % has expired.';

-- War end tick. Wars have a fixed length of 48 ticks, but just to be safe, see
-- if we can't find an explicit end tick.
UPDATE utmp AS main
SET relation_end_tick = other.tick
FROM utmp AS other
WHERE ((other.alliance1_id = main.alliance1_id AND other.alliance2_id = main.alliance2_id)
       OR
       (other.alliance1_id = main.alliance2_id AND other.alliance2_id = main.alliance1_id))
AND main.relation_type = 'War'
AND other.tick > main.tick
AND other.text ILIKE '%''s war with % has expired.';

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_userfeed();
CREATE FUNCTION store_userfeed(curround smallint) RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('utmp','type');
PERFORM trim_quotes('utmp','text');

--transfer tmp to dump
INSERT INTO userfeed_dump (round,tick,type,text)
SELECT curround,tick,type,text FROM utmp
ON CONFLICT DO NOTHING;

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
INSERT INTO anarchy (round, start_tick, end_tick, pid)
SELECT curround, tick, anarchy_end_tick, pid FROM utmp WHERE anarchy_end_tick IS NOT NULL AND pid IS NOT NULL
ON CONFLICT DO NOTHING;

-- Extract alliance relation data.
ALTER TABLE utmp ADD COLUMN relation_type varchar(4);
ALTER TABLE utmp ADD COLUMN alliance1_id integer;
ALTER TABLE utmp ADD COLUMN alliance2_id integer;
ALTER TABLE utmp ADD COLUMN relation_end_tick smallint DEFAULT 32767;

PERFORM analyze_naps(curround);
PERFORM analyze_alliances(curround);
PERFORM analyze_wars(curround);

-- Transfer alliance relation data. Clear and refill the data for the round
-- every tick. If either alliance is unknown (probably because Munin misses
-- ticks), don't insert.
DELETE FROM alliance_relation WHERE round = curround;
INSERT INTO alliance_relation (round, start_tick, type, end_tick, initiator, acceptor)
SELECT curround, tick, relation_type, relation_end_tick, alliance1_id, alliance2_id FROM utmp
WHERE relation_type IS NOT NULL
AND alliance1_id IS NOT NULL
AND alliance2_id IS NOT NULL;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS store_update(smallint,text,text,text,text);
CREATE FUNCTION store_update(curround smallint,curtick smallint,ptable text,gtable text,atable text,utable text) RETURNS void AS $PROC$
BEGIN
INSERT INTO updates (round,tick,planets,galaxies,alliances,userfeed)
VALUES (curround,
        curtick,
        (SELECT COUNT(*) FROM quote_ident(ptable)),
        (SELECT COUNT(*) FROM quote_ident(gtable)),
        (SELECT COUNT(*) FROM quote_ident(atable)),
        (SELECT COUNT(*) FROM quote_ident(utable))
       );
END
$PROC$ LANGUAGE plpgsql;


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
    AND landing_tick = NEW.landing_tick;

    IF defcall_id > 0 THEN
        UPDATE defcalls SET status = 3 WHERE id = defcall_id;
    ELSE
        INSERT INTO defcalls (status, round, target, landing_tick) VALUES (2, NEW.round, NEW.target, NEW.landing_tick);
    END IF;
END IF;

RETURN NEW;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE;
ALTER FUNCTION defcall_update() OWNER TO munin;


DROP FUNCTION gal_value(smallint,smallint);
