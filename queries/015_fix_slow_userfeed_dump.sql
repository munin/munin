-- Backwards compatibility for single-round Munin
DROP FUNCTION IF EXISTS store_userfeed();
DROP FUNCTION IF EXISTS store_userfeed(smallint);
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
UPDATE utmp SET pid=p.id FROM planet_dump AS p WHERE utmp.x = p.x AND utmp.y = p.y AND utmp.z = p.z AND utmp.tick = p.tick AND p.round=curround;

--transfer anarchy data, exclude exit anarchy entries
INSERT INTO anarchy (round, start_tick, end_tick, pid)
SELECT curround, tick, anarchy_end_tick, pid FROM utmp WHERE anarchy_end_tick IS NOT NULL AND pid IS NOT NULL
ON CONFLICT DO NOTHING;

-- Extract alliance relation data.
ALTER TABLE utmp ADD COLUMN relation_type text;
ALTER TABLE utmp ADD COLUMN alliance1_id integer;
ALTER TABLE utmp ADD COLUMN alliance2_id integer;
ALTER TABLE utmp ADD COLUMN relation_end_tick smallint DEFAULT 32767;

PERFORM analyze_naps(curround);
PERFORM analyze_alliances(curround);
PERFORM analyze_wars(curround);
PERFORM analyze_auto_wars(curround);

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
