-- Support military and incoming scans. Note that there is no table for incoming
-- scans.
ALTER TABLE public.scan DROP CONSTRAINT scan_scantype_check;
ALTER TABLE public.scan ADD CONSTRAINT scan_scantype_check CHECK (scantype::text = ANY (ARRAY[
    'unknown'::character varying::text,
    'planet'::character varying::text,
    'development'::character varying::text,
    'unit'::character varying::text,
    'news'::character varying::text,
    'incoming'::character varying::text,
    'jgp'::character varying::text,
    'fleet'::character varying::text,
    'au'::character varying::text,
    'military'::character varying::text
]));
CREATE TABLE military
(
    id serial PRIMARY KEY,
    scan_id bigint NOT NULL REFERENCES scan(id),
    fleet_index smallint NOT NULL CHECK(fleet_index in (0, 1, 2, 3)),
    ship_id integer NOT NULL REFERENCES ship(id),
    amount integer NOT NULL
);

-- Don't include fleet_size in the UNIQUE CONSTRAINT: on 'Launch' news scan
-- entries the fleet size is NULL, which does not result in violations of the
-- UNIQUE CONSTRAINT (because NULL is never equal to NULL), which, in practice
-- results in duplicate entries that we don't want.
--
-- A similar problem occurs with the mission column: on JGPs and outgoing fleets
-- on news scans, that's either 'attack', 'defend', or 'return', but that
-- information is not included for incoming fleets on news scans. Previously,
-- Munin set those to 'unknown', but this means that if the same fleet is seen
-- on a JGP and a news scan, that results in yet more duplicate entries.
--
-- Loosening the constraint like this widens the already-existing possibility
-- that Munin will mix up fleets from JGPs and news scans when someone swaps the
-- name of 2 fleets with the same target and landing tick. Previously, that only
-- confused Munin if the two fleets also had the same mission and the number of
-- visible ships in them. In practice, though, this confusion has no visible
-- effects: fleet information is only ever used by INNER JOINing with a JGP row
-- in the scan table, at which point everything resolves gracefully.
ALTER TABLE fleet
DROP CONSTRAINT fleet_owner_id_target_fleet_size_fleet_name_round_landing_t_key;
ALTER TABLE fleet
ADD UNIQUE(owner_id, target, fleet_name, round, landing_tick)
