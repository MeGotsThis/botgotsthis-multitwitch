CREATE TABLE multitwitch (
    broadcaster VARCHAR NOT NULL PRIMARY KEY,
    twitchgroup VARCHAR NOT NULL,
    addedTime TIMESTAMP NOT NULL,
    lastLive TIMESTAMP NULL,
    isEvent BOOLEAN NOT NULL DEFAULT '0'
);
CREATE INDEX multitwitch_twitchgroup ON multitwitch (twitchgroup);
