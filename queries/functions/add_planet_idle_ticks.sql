DROP FUNCTION IF EXISTS add_planet_idle_ticks(smallint);
DROP FUNCTION IF EXISTS add_planet_idle_ticks(smallint, smallint);
CREATE FUNCTION add_planet_idle_ticks(curround smallint, curtick smallint) RETURNS void AS $PROC$
BEGIN
ALTER TABLE ptmp ADD COLUMN idle smallint DEFAULT 0;
ALTER TABLE ptmp ADD COLUMN vdiff integer DEFAULT 0;

UPDATE ptmp SET vdiff = ptmp.value - t2.value
FROM planet_dump AS t2
WHERE ptmp.id=t2.id AND t2.tick=curtick-1 AND t2.round=curround;

UPDATE ptmp SET idle = t2.idle + 1
FROM planet_dump AS t2
WHERE ptmp.id=t2.id AND t2.tick=curtick-1 AND ptmp.vdiff >= t2.vdiff - 1 AND ptmp.vdiff <= t2.vdiff + 1 AND ptmp.xp - t2.xp = 0 AND t2.round=curround;
END
$PROC$ LANGUAGE plpgsql;
