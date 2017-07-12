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
