CREATE TABLE multitwitch (
    broadcaster VARCHAR NOT NULL PRIMARY KEY,
    twitchgroup VARCHAR NOT NULL,
    addedTime TIMESTAMP NOT NULL,
    lastLive TIMESTAMP NULL,
    isEvent BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX multitwitch_twitchgroup ON multitwitch (twitchgroup);
