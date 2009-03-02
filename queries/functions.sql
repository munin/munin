
-- Since the plpythonu language is unrestricted, functions must be created as
-- superuser. This is somewhat undesirable. Poop.
/*CREATE FUNCTION test(table) RETURNS text AS $PROC$
return args[0]
$PROC$ LANGUAGE 'plpythonu';*/

-- BEGIN HUGIN RELATED FUNCTIONS

DROP FUNCTION trim_quotes(text,text);
CREATE FUNCTION trim_quotes(tmptab text,colname text) RETURNS void AS $PROC$
BEGIN
EXECUTE 'UPDATE '||tmptab||' SET '||colname||'=trim(''"'' FROM '||colname||')';
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION gen_planet_id();
CREATE FUNCTION gen_planet_id() RETURNS void AS $PROC$
DECLARE
r RECORD;
BEGIN
-- deactive missing
UPDATE planet_canon SET active=FALSE WHERE ROW(rulername,planetname) NOT IN (SELECT rulername,planetname FROM ptmp);
-- insert new into canonical and update IDs
INSERT INTO planet_canon (rulername,planetname) SELECT t1.rulername,t1.planetname FROM ptmp AS t1 WHERE ROW(t1.rulername,t1.planetname) NOT IN (SELECT rulername,planetname FROM planet_canon);
-- insert IDs for existing
ALTER TABLE ptmp ADD COLUMN id integer DEFAULT -1;
UPDATE ptmp SET id=t1.id FROM planet_canon AS t1 WHERE ptmp.rulername=t1.rulername AND ptmp.planetname=t1.planetname;
CREATE INDEX ptmp_id_index ON ptmp(id);
ANALYZE ptmp;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION gen_galaxy_id();
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
--FOR r IN EXECUTE 'SELECT x,y FROM '||tmptab||' INTERSECT (SELECT x,y FROM galaxy_canon)' LOOP
-- EXECUTE 'UPDATE '||tmptab||' SET id=(SELECT id FROM galaxy_canon WHERE x='||r.x||' AND y='||r.y||')';
--END LOOP;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION gen_alliance_id();
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

--FOR r IN EXECUTE 'SELECT name FROM '||tmptab||' INTERSECT (SELECT name FROM alliance_canon)' LOOP
-- EXECUTE 'UPDATE '||tmptab||' SET id=(SELECT id FROM alliance_canon WHERE name='||r.name||')';
--END LOOP;
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION add_rank(text,text);
CREATE FUNCTION add_rank(tmptab text,colname text) RETURNS void AS $PROC$
DECLARE
r RECORD;
rank INT := 0;
BEGIN
EXECUTE 'ALTER TABLE '||quote_ident(tmptab)||' ADD COLUMN '||quote_ident(colname)||'_rank smallint DEFAULT -1';
/*PERFORM setval('rank_seq',1,false);
EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(colname)||'_rank=nextval(\'rank_seq\')
FROM (SELECT id FROM '||quote_ident(tmptab)||' ORDER BY '||quote_ident(colname)||' DESC) AS t1
WHERE '||quote_ident(tmptab)||'.id=t1.id';*/
FOR r IN EXECUTE 'SELECT id FROM '||quote_ident(tmptab)||' ORDER BY '||quote_ident(colname)||' DESC' LOOP
 rank := rank + 1;
 EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(colname)||'_rank='||rank||' WHERE id='||r.id;
END LOOP;

END
$PROC$ LANGUAGE plpgsql;

--CREATE TEMP SEQUENCE rank;
--PERFORM setval('rank',1,false);



DROP FUNCTION add_average(text,text,text,text);
CREATE FUNCTION add_average(tmptab text,value_colname text,quantity_colname text,coltype text) RETURNS void AS $PROC$
BEGIN
EXECUTE 'ALTER TABLE '||quote_ident(tmptab)||' ADD COLUMN '||quote_ident(value_colname)||'_avg '||coltype||' DEFAULT -1';
EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(value_colname)||'_avg='||quote_ident(value_colname)||'::bigint/'||quote_ident(quantity_colname)||'::bigint';
END
$PROC$ LANGUAGE plpgsql;


-- PLANET SPECIFIC RANK FUNCTIONS FOR PERFORMANCE

DROP FUNCTION add_rank_planet_size();
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

DROP FUNCTION add_rank_planet_score();
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

DROP FUNCTION add_rank_planet_value();
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

DROP FUNCTION add_rank_planet_xp();
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


DROP FUNCTION add_planet_idle_ticks(smallint);
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


DROP FUNCTION store_planets(smallint);
CREATE FUNCTION store_planets(curtick smallint) RETURNS void AS $PROC$
DECLARE
 r RECORD;
BEGIN
	--remove quotes from names added by the dumpfile generator

	PERFORM trim_quotes('ptmp','rulername');
	PERFORM trim_quotes('ptmp','planetname');
	--generate IDs, insert missing into canonical, deactive missing planets

	PERFORM gen_planet_id();

/*	CREATE TEMP SEQUENCE rank_seq ;
	PERFORM add_rank('ptmp','size');
	PERFORM add_rank('ptmp','score');
	PERFORM add_rank('ptmp','value');
	PERFORM add_rank('ptmp','xp');*/

	--generate ranks, this will add the appropriate columns to the temp table

	PERFORM add_rank_planet_size();
	PERFORM add_rank_planet_score();
	PERFORM add_rank_planet_value();
	PERFORM add_rank_planet_xp();
	PERFORM add_planet_idle_ticks(curtick);
	--ALTER TABLE ptmp ADD COLUMN idle smallint DEFAULT 0;
	--ALTER TABLE ptmp ADD COLUMN vdiff integer DEFAULT 0;

	--transfer temporary data into permanent dump
	INSERT INTO planet_dump (tick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id)
		SELECT curtick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id FROM ptmp;

END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION store_galaxies(smallint);
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
		SELECT curtick,x,y,name,size,score,value,xp,size_rank,score_rank,value_rank,xp_rank,id FROM gtmp;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_alliances(smallint);
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

        --generate ranks
        PERFORM add_rank('atmp','size');
--        PERFORM add_rank('atmp','score');
        PERFORM add_rank('atmp','members');
        PERFORM add_rank('atmp','size_avg');
        PERFORM add_rank('atmp','score_avg');


        --transfer tmp to dump
	INSERT INTO alliance_dump (tick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,id)
		SELECT curtick,name,size,members,score,size_avg,score_avg,size_rank,members_rank,score_rank,size_avg_rank,score_avg_rank,id FROM atmp;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_update(smallint,text,text,text);
CREATE FUNCTION store_update(curtick smallint,ptable text,gtable text,atable text) RETURNS void AS $PROC$
BEGIN
	INSERT INTO updates (tick,planets,galaxies,alliances) VALUES (curtick,(SELECT COUNT(*) FROM quote_ident(ptable)),(SELECT COUNT(*) FROM quote_ident(gtable)),(SELECT COUNT(*) FROM quote_ident(atable)));
END
$PROC$ LANGUAGE plpgsql;

-- END HUGIN RELATED FUNCTIONS

-- Function: defcall_update()

DROP FUNCTION defcall_update();

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

DROP FUNCTION max_tick();
CREATE FUNCTION max_tick() RETURNS int AS $PROC$
BEGIN
RETURN MAX(tick) FROM updates;
END
$PROC$ LANGUAGE plpgsql;

DROP FUNCTION gal_value(smallint,smallint);
CREATE FUNCTION gal_value(gal_x smallint, gal_y smallint) RETURNS int AS $PROC$
BEGIN
RETURN sum(value) FROM planet_dump
WHERE tick=(SELECT max_tick()) AND x=gal_x AND y=gal_y
GROUP BY x,y;
END
$PROC$ LANGUAGE plpgsql;



-- END MUNIN RELATED FUNCTIONS
/*END;
BEGIN

EXCEPTION

END;*/
