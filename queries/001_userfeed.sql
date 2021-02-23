ALTER TABLE updates
ADD COLUMN userfeed smallint DEFAULT -1;

CREATE TABLE userfeed_dump (
  tick smallint,
  type varchar(32) NOT NULL,
  text varchar(255) NOT NULL,
  PRIMARY KEY(tick, text)
);
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


DROP FUNCTION IF EXISTS store_userfeed();
CREATE FUNCTION store_userfeed() RETURNS void AS $PROC$
BEGIN
--remove quotes from names added by the dumpfile generator
PERFORM trim_quotes('utmp','type');
PERFORM trim_quotes('utmp','text');

--transfer tmp to dump
INSERT INTO userfeed_dump (tick,type,text)
SELECT tick,type,text FROM utmp
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
INSERT INTO anarchy (start_tick, end_tick, pid)
SELECT tick, anarchy_end_tick, pid FROM utmp WHERE anarchy_end_tick IS NOT NULL AND pid IS NOT NULL
ON CONFLICT DO NOTHING;

END
$PROC$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS store_update(smallint,text,text,text);
DROP FUNCTION IF EXISTS store_update(smallint,text,text,text,text);
CREATE FUNCTION store_update(curtick smallint,ptable text,gtable text,atable text,utable text) RETURNS void AS $PROC$
BEGIN
INSERT INTO updates (tick,planets,galaxies,alliances,userfeed) VALUES (curtick,(SELECT COUNT(*) FROM quote_ident(ptable)),(SELECT COUNT(*) FROM quote_ident(gtable)),(SELECT COUNT(*) FROM quote_ident(atable)),(SELECT COUNT(*) FROM quote_ident(utable)));
END
$PROC$ LANGUAGE plpgsql;
