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
--EXECUTE 'SELECT t1.rulername,t1.planetname FROM '||quote_ident(tmptab)||' AS t1 WHERE ROW(t1.rulername,t1.planetname) NOT IN (SELECT rulername,planetname FROM planet_canon)' INTO r;
--RAISE EXCEPTION 'Foo: %',r;
INSERT INTO planet_canon (rulername,planetname) SELECT t1.rulername,t1.planetname FROM ptmp AS t1 WHERE ROW(t1.rulername,t1.planetname) NOT IN (SELECT rulername,planetname FROM planet_canon);
-- insert IDs for existing
ALTER TABLE ptmp ADD COLUMN id integer DEFAULT -1;
UPDATE ptmp SET id=t1.id FROM planet_canon AS t1 WHERE ptmp.rulername=t1.rulername AND ptmp.planetname=t1.planetname;

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
--CREATE TEMP SEQUENCE rank;
--PERFORM setval('rank',1,false);

FOR r IN EXECUTE 'SELECT id FROM '||quote_ident(tmptab)||' ORDER BY '||quote_ident(colname)||' DESC' LOOP
 rank := rank + 1;
-- RAISE EXCEPTION 'r: %,rank: %',r,rank;
 EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(colname)||'_rank='||rank||' WHERE id='||r.id;
END LOOP;
-- This is broken, can't do ordering in UPDATE. Perhaps a subquery can fix this?
--EXECUTE 'UPDATE '||tmptab||' SET '||colname||'_rank = nextval(''rank'') FROM tmptab AS t1 JOIN tmptab AS t2 ON t1.x=t2.x AND t1.y=t2.y AND t1.z=t2.z ORDER BY t1.'||colname||' DESC';
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION add_average(text,text,text,text);
CREATE FUNCTION add_average(tmptab text,value_colname text,quantity_colname text,coltype text) RETURNS void AS $PROC$
BEGIN
EXECUTE 'ALTER TABLE '||quote_ident(tmptab)||' ADD COLUMN '||quote_ident(value_colname)||'_avg '||coltype||' DEFAULT -1';
EXECUTE 'UPDATE '||quote_ident(tmptab)||' SET '||quote_ident(value_colname)||'_avg='||quote_ident(value_colname)||'::bigint/'||quote_ident(quantity_colname)||'::bigint';
END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION store_planets(smallint);
CREATE FUNCTION store_planets(curtick smallint) RETURNS void AS $PROC$
BEGIN 
	--remove quotes from names added by the dumpfile generator
	PERFORM trim_quotes('ptmp','rulername');
	PERFORM trim_quotes('ptmp','planetname');
	--generate IDs, insert missing into canonical, deactive missing planets
	PERFORM gen_planet_id();
	--generate ranks, this will add the appropriate columns to the temp table
	PERFORM add_rank('ptmp','size');
	PERFORM add_rank('ptmp','score');
	PERFORM add_rank('ptmp','value');
	PERFORM add_rank('ptmp','xp');

	--transfer temporary data into permanent dump 
	INSERT INTO planet_dump (tick,x,y,z,planetname,rulername,race,size,score,value,xp,size_rank,score_rank,value_rank,xp_rank,id)
		SELECT curtick,x,y,z,planetname,rulername,race,size,score,value,xp,size_rank,score_rank,value_rank,xp_rank,id FROM ptmp;
	   
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

-- BEGIN MUNIN RELATED FUNCTIONS

DROP TYPE munin_return CASCADE;
CREATE TYPE munin_return AS (success BOOLEAN, retmessage TEXT);

--DROP FUNCTION sponsor(text,text,text);
CREATE FUNCTION sponsor(inviter text,recruit text,comment_text text) RETURNS munin_return AS $PROC$
DECLARE
	ret munin_return%ROWTYPE;
BEGIN
UPDATE user_pref SET invites=invites-1 WHERE id=(SELECT id FROM user_list WHERE pnick=inviter);
INSERT INTO sponsor (pnick,sponsor_id,comment) VALUES (recruit,(SELECT id FROM user_list WHERE pnick=inviter),comment_text);
ret := ROW(TRUE,recruit ||' sponsored');
RETURN ret;
EXCEPTION
	WHEN check_violation THEN
		ret := ROW(FALSE,'Not enough invites');
		RETURN ret;
	WHEN integrity_constraint_violation THEN
		ret := ROW(FALSE,recruit ||' already sponsored');
		RETURN ret;
END
$PROC$ LANGUAGE plpgsql;


CREATE FUNCTION unsponsor(inviter text,recruit text) RETURNS munin_return AS $PROC$
DECLARE
        ret munin_return%ROWTYPE;
	r RECORD;
BEGIN
--RAISE EXCEPTION 'Foo %',quote_literal(inviter);
SELECT INTO r sponsor.id AS id,count(sponsor.id) AS count FROM sponsor WHERE pnick=recruit AND sponsor_id=(SELECT id FROM user_list WHERE pnick=inviter) GROUP BY id;
IF r.count > 0 THEN 
	DELETE FROM sponsor WHERE id=r.id;
	UPDATE user_pref SET invites=invites+1 WHERE id=(SELECT id FROM user_list WHERE pnick=inviter);
	ret=ROW(TRUE,'Removed sponsorship of '||recruit);
	RETURN ret;
ELSE
	ret=ROW(FALSE,'No sponsorships matching '||recruit);
	RETURN ret;
END IF;
END
$PROC$ LANGUAGE plpgsql;


CREATE FUNCTION invite(inviter text,recruit text) RETURNS munin_return AS $PROC$
DECLARE
        ret munin_return%ROWTYPE;
        r RECORD;
BEGIN
SELECT INTO r EXTRACT(HOUR FROM now() - t1.timestamp) AS age,t1.pnick AS gimp,t2.pnick AS sponsor 
	FROM sponsor AS t1 INNER JOIN user_list AS t2 ON t1.sponsor_id=t2.id 
	WHERE t1.pnick=recruit AND t2.pnick=inviter LIMIT 1;
IF r.age > 36 THEN
	INSERT INTO user_list (userlevel,pnick,sponsor) VALUES (100,recruit,inviter);
	DELETE FROM sponsor WHERE pnick=r.gimp;
	ret=ROW(TRUE,recruit||' successfully invited');
       	RETURN ret;	
ELSIF r.age <= 36 THEN
	ret=ROW(FALSE,'Sponsorship of '||recruit||' has only stood for '||r.age||' hours, needs to stand for 36 hours');
	RETURN ret;
ELSE
        ret=ROW(FALSE,'No sponsorships matching gimp: '||recruit||', sponsor: '||inviter) ;
        RETURN ret;
END IF;
EXCEPTION
	WHEN integrity_constraint_violation THEN 
		UPDATE user_list SET userlevel=100, sponsor=inviter WHERE pnick=recruit;
		DELETE FROM sponsor WHERE pnick=r.gimp;
		ret=ROW(TRUE,recruit||' successfully invited');
		RETURN ret;
END
$PROC$ LANGUAGE plpgsql;




-- END MUNIN RELATED FUNCTIONS
/*END;
BEGIN

EXCEPTION

END;*/