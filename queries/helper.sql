

--;select  x,y,z,t2.tick,wave_amplifier,wave_distorter,t4.nick,t5.name
--;from development t1 
--;inner join scan t2 on t1.scan_id=t2.id 
--;inner join planet_dump t3 on t2.pid=t3.id 
--;left join intel t4 on t3.id=t4.pid
--;left join alliance_canon t5 on t4.alliance_id=t5.id
--;where (wave_amplifier > 1 OR wave_distorter > 1) 
--;and t3.tick=(select max_tick())
--;order by t2.tick asc;

select  x,y,z,res_metal,res_crystal,res_eonium,t2.tick,t4.nick,t5.name
from planet t1
inner join scan t2 on t1.scan_id=t2.id
inner join planet_dump t3 on t2.pid=t3.id
left join intel t4 on t3.id=t4.pid
left join alliance_canon t5 on t4.alliance_id=t5.id
where guards < 400
and t3.tick=(select max_tick())
and (res_eonium + res_crystal + res_metal) >= 3000000
and t3.value >= 400000
order by t2.tick asc;

