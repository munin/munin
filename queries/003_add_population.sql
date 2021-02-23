ALTER TABLE development ADD COLUMN population smallint NOT NULL DEFAULT 5;
ALTER TABLE development ALTER COLUMN population DROP DEFAULT;
