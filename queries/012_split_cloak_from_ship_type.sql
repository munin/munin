ALTER TABLE public.ship ADD COLUMN is_cloaked boolean NOT NULL DEFAULT FALSE;
UPDATE ship SET is_cloaked = TRUE WHERE ship.type = 'Cloak';
UPDATE ship SET type = 'Norm' WHERE ship.type = 'Cloak';

ALTER TABLE public.ship DROP CONSTRAINT ship_type_check;
ALTER TABLE public.ship ADD CONSTRAINT ship_type_check CHECK (type::text = ANY (ARRAY[
    'Norm'::character varying::text,
    'Pod'::character varying::text,
    'Struc'::character varying::text,
    'Emp'::character varying::text,
    'Steal'::character varying::text,
    'Res'::character varying::text
]))
