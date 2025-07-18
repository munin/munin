-- Improve the performance of these functions by allowing PostgreSQL to only
-- execute them once per query.
ALTER FUNCTION max_round() STABLE;
ALTER FUNCTION max_tick(smallint) STABLE;
