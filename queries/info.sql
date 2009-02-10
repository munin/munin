SELECT sum(t1.size)-sum(t2.size) FROM planet_dump AS t1 INNER JOIN planet_dump AS t2 ON t1.id=t2.id AND t1.tick=t2.tick+14 INNER JOIN intel AS t3 on t1.id=t3.pid WHERE t1.tick=(SELECT max_tick()) AND t3.alliance_id=23;


