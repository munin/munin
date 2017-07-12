DROP FUNCTION IF EXISTS store_planets(smallint);
DROP FUNCTION IF EXISTS store_planets(smallint, smallint);
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
PERFORM add_planet_idle_ticks(curround, curtick);

--transfer temporary data into permanent dump
INSERT INTO planet_dump (round,tick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id)
SELECT curround,curtick,x,y,z,planetname,rulername,race,size,score,value,xp,idle,vdiff,size_rank,score_rank,value_rank,xp_rank,id FROM ptmp;

END
$PROC$ LANGUAGE plpgsql;
