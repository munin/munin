SELECT sum(t1.size)-sum(t2.size) FROM planet_dump AS t1 INNER JOIN planet_dump AS t2 ON t1.id=t2.id AND t1.tick=t2.tick+14 INNER JOIN intel AS t3 on t1.id=t3.pid WHERE t1.tick=(SELECT max_tick()) AND t3.alliance_id=11;

SELECT t1.x,t1.y,t1.z,t1.size AS planet_value, t1.score AS planet_score, t1.value AS planet_value,t1.race AS race,t2.value_rank AS gal_val_rank,t3.nick
FROM planet_dump t1
INNER JOIN galaxy_dump t2 ON t1.x=t2.x AND t1.y=t2.y AND t1.tick=t2.tick 
INNER JOIN intel t3 ON t1.id=t3.pid 
WHERE t1.tick=(SELECT max_tick()) AND t3.alliance_id=11
ORDER BY t1.size DESC;



