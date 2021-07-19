ALTER TABLE user_list       ALTER COLUMN pnick      TYPE text;
ALTER TABLE user_list       ALTER COLUMN alias_nick TYPE text;
ALTER TABLE user_list       ALTER COLUMN sponsor    TYPE text;

ALTER TABLE target          ALTER COLUMN nick       TYPE text;

ALTER TABLE intel           ALTER COLUMN nick       TYPE text;
ALTER TABLE intel           ALTER COLUMN fakenick   TYPE text;

ALTER TABLE scan            ALTER COLUMN nick       TYPE text;
ALTER TABLE scan            ALTER COLUMN pnick      TYPE text;

ALTER TABLE defcalls        ALTER COLUMN claimed_by TYPE text;

ALTER TABLE command_log     ALTER COLUMN nick       TYPE text;
ALTER TABLE command_log     ALTER COLUMN pnick      TYPE text;

ALTER TABLE froglet_logs    ALTER COLUMN pnick      TYPE text;

ALTER TABLE invite_proposal ALTER COLUMN person     TYPE text;
