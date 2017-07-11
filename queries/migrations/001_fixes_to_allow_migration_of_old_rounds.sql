ALTER TABLE planet_canon ALTER COLUMN uid VARCHAR(255);

ALTER TABLE planet_dump ALTER COLUMN uid VARCHAR(255);

ALTER TABLE planet_dump DROP CONSTRAINT planet_dump_uid_fkey;

CREATE INDEX planet_dump_id_index ON planet_dump(id);

ALTER TABLE scan DROP CONSTRAINT scan_round_fkey;
