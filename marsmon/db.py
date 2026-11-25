"""Local SQLite store. Rebuilt from the public feeds, so it is not committed."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "marsmon.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    rover TEXT NOT NULL,
    imageid TEXT NOT NULL,
    sol INTEGER,
    camera TEXT,
    taken_utc TEXT,
    lmst TEXT,
    received_utc TEXT,
    site INTEGER,
    drive INTEGER,
    width INTEGER,
    height INTEGER,
    mast_az REAL,
    mast_el REAL,
    sample_type TEXT,
    url_small TEXT,
    url_medium TEXT,
    url_large TEXT,
    url_full TEXT,
    credit TEXT,
    ls REAL,
    mars_year INTEGER,
    PRIMARY KEY (rover, imageid)
);
CREATE INDEX IF NOT EXISTS images_stop ON images (rover, site, drive);
CREATE INDEX IF NOT EXISTS images_cam_sol ON images (rover, camera, sol);

CREATE TABLE IF NOT EXISTS stops (
    rover TEXT NOT NULL,
    site INTEGER NOT NULL,
    drive INTEGER NOT NULL,
    sol INTEGER,
    lat REAL,
    lon REAL,
    elev_m REAL,
    odometer_m REAL,      -- cleaned: running maximum of the published total distance
    published_total_m REAL,
    final INTEGER,        -- 1 if the feed marks this as the end-of-drive position
    ls REAL,
    mars_year INTEGER,
    PRIMARY KEY (rover, site, drive)
);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=60)  # several ingest ranges may write at once
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
