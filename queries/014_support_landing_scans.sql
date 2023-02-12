ALTER TABLE public.scan DROP CONSTRAINT scan_scantype_check;
ALTER TABLE public.scan ADD CONSTRAINT scan_scantype_check CHECK (scantype::text = ANY (ARRAY[
    'unknown'::character varying::text,
    'planet'::character varying::text,
    'landing'::character varying::text,
    'development'::character varying::text,
    'unit'::character varying::text,
    'news'::character varying::text,
    'incoming'::character varying::text,
    'jgp'::character varying::text,
    'fleet'::character varying::text,
    'au'::character varying::text,
    'military'::character varying::text
]));
