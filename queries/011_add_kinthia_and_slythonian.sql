ALTER TABLE public.ship DROP CONSTRAINT ship_race_check;
ALTER TABLE public.ship ADD CONSTRAINT ship_race_check CHECK (race::text = ANY (ARRAY[
    'Terran'::character varying::text,
    'Cathaar'::character varying::text,
    'Xandathrii'::character varying::text,
    'Zikonian'::character varying::text,
    'Eitraides'::character varying::text,
    'Kinthia'::character varying::text,
    'Slythonian'::character varying::text
]));

ALTER TABLE public.planet_dump DROP CONSTRAINT planet_dump_race_check;
ALTER TABLE public.planet_dump ADD CONSTRAINT planet_dump_race_check CHECK (race = ANY (ARRAY[
    'Ter'::bpchar,
    'Cat'::bpchar,
    'Xan'::bpchar,
    'Zik'::bpchar,
    'Etd'::bpchar,
    'Kin'::bpchar,
    'Sly'::bpchar
]));
