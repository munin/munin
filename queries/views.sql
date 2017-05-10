DROP VIEW IF EXISTS latest_tick;
CREATE VIEW latest_tick AS
SELECT t1.id AS id, t1.planetname AS planetname, t1.rulername AS rulername, t2.nick AS nick,
    t2.fakenick AS fakenick, t2.defwhore AS defwhore, t2.gov AS gov, t2.bg AS bg, t2.covop AS covop,
    t2.reportchan AS reportchan, t2.scanner AS scanner, t2.distwhore AS distwhore, t2.comment AS comment,
    t2.relay AS relay, t2.nap AS nap, t3.name AS alliance,
    t4.x AS x, t4.y AS y, t4.z AS z, t4.race AS race, t4.size AS size, t4.score AS score, t4.value AS value,
    t4.score_rank AS score_rank, t4.xp AS xp, t4.xp_rank AS xp_rank, t4.idle AS idle, t4.vdiff AS vdiff,
    t5.epenis AS epenis, t5.epenis_rank AS epenis_rank
FROM planet_canon AS t1
LEFT JOIN intel AS t2 ON t1.id=t2.pid
LEFT JOIN alliance_canon AS t3 ON t2.alliance_id=t3.id
INNER JOIN planet_dump AS t4 ON t1.id=t4.id
LEFT JOIN epenis_cache AS t5 ON t1.id=t5.planet_id
WHERE t4.tick = (SELECT max_tick(71))
AND t4.round = 71
;

