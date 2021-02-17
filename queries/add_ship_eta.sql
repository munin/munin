BEGIN;

ALTER TABLE ship
ADD COLUMN eta smallint NOT NULL
DEFAULT 999;

UPDATE ship
SET eta = 8
WHERE class IN ('Fighter', 'Corvette');

UPDATE ship
SET eta = 9
WHERE class IN ('Frigate', 'Destroyer');

UPDATE ship
SET eta = 10
WHERE class IN ('Cruiser', 'Battleship');

ALTER TABLE ship
ALTER COLUMN eta
DROP DEFAULT;


COMMIT;
