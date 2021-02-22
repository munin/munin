-- Make room for alliance relation type 'Auto-War'.
ALTER TABLE alliance_relation
ALTER COLUMN type TYPE text;





-- Backwards compatibility for single-round Munin
DROP FUNCTION IF EXISTS analyze_wars();
DROP FUNCTION IF EXISTS analyze_wars(curround smallint);
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
WHERE other.alliance1_id = main.alliance1_id
AND   other.alliance2_id = main.alliance2_id
AND main.relation_type = 'War'
AND other.tick > main.tick
AND other.text ILIKE '%''s war with % has expired.';

END
$PROC$ LANGUAGE plpgsql;





DROP FUNCTION IF EXISTS analyze_auto_wars(curround smallint);
CREATE FUNCTION analyze_auto_wars(curround smallint) RETURNS void AS $PROC$
BEGIN

-- War start and default end tick.
UPDATE utmp AS main SET relation_type='Auto-War',
alliance1_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '(.*) has automatically declared war on .* due to long-standing aggression !')
              AND tick = main.tick
              AND round = curround),
alliance2_id=(SELECT id FROM alliance_canon
              WHERE name = substring(text from '.* has automatically declared war on (.*) due to long-standing aggression !')
              AND tick = main.tick
              AND round = curround),
relation_end_tick=(tick+96) -- Auto-wars have a fixed length of 96 ticks.
WHERE text ILIKE '% has automatically declared war on % due to long-standing aggression !';

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

-- Auto-War end tick. Auto-Wars have a fixed length of 96 ticks, but just to be
-- safe, see if we can't find an explicit end tick.
UPDATE utmp AS main
SET relation_end_tick = other.tick
FROM utmp AS other
WHERE other.alliance1_id = main.alliance1_id
AND   other.alliance2_id = main.alliance2_id
AND main.relation_type = 'Auto-War'
AND other.tick > main.tick
AND other.text ILIKE '%''s war with % has expired.';

END
$PROC$ LANGUAGE plpgsql;





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
UPDATE utmp SET pid=p.id FROM planet_dump AS p WHERE utmp.x = p.x AND utmp.y = p.y AND utmp.z = p.z AND utmp.tick = p.tick;

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

-- Backwards compatibility for pre-userfeed Munin
DROP FUNCTION IF EXISTS store_update(smallint,text,text,text);
-- Backwards compatibility for single-round Munin
DROP FUNCTION IF EXISTS store_update(smallint,text,text,text,text);
DROP FUNCTION IF EXISTS store_update(smallint,smallint,text,text,text,text);
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
