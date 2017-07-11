ALTER TABLE planet_canon ALTER COLUMN uid TYPE VARCHAR(255);

ALTER TABLE planet_dump ALTER COLUMN uid TYPE VARCHAR(255);

ALTER TABLE planet_dump DROP CONSTRAINT planet_dump_uid_fkey;

ALTER TABLE scan DROP CONSTRAINT scan_round_fkey;
