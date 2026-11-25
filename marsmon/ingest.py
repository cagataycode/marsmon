"""Pull image metadata and route stops into the local database.

    python3 -m marsmon.ingest route --rover m20
    python3 -m marsmon.ingest images --rover m20 --camera NAVCAM_LEFT            # whole mission
    python3 -m marsmon.ingest images --rover m20 --camera NAVCAM_LEFT --recent 5  # last 5 sols only
    python3 -m marsmon.ingest images --rover m20 --camera NAVCAM_LEFT --before-sol 1548  # resume

Only metadata is stored; images are referenced by URL, never downloaded here.
"""
import argparse
import sys

from . import api, db, seasons

IMAGE_COLS = ["rover", "imageid", "sol", "camera", "taken_utc", "lmst", "received_utc", "site", "drive",
              "width", "height", "mast_az", "mast_el", "sample_type", "url_small", "url_medium", "url_large",
              "url_full", "credit", "ls", "mars_year"]


def _with_season(rec: dict) -> dict:
    try:
        t = seasons.parse_utc(rec["taken_utc"])
        rec["ls"] = round(seasons.ls(t), 3)
        rec["mars_year"] = seasons.mars_year(t)
    except Exception:
        rec["ls"] = rec["mars_year"] = None
    return rec


def ingest_images(rover: str, camera: str | None, recent: int | None = None, before_sol: int | None = None,
                  from_sol: int | None = None) -> int:
    if rover != "m20":
        raise SystemExit("Only Perseverance (m20) images are wired up so far.")
    con = db.connect()
    sol_min = from_sol
    if recent is not None:
        row = con.execute("SELECT MAX(sol) FROM images WHERE rover=? AND (? IS NULL OR camera=?)", (rover, camera, camera)).fetchone()
        sol_min = (row[0] or 0) - recent
    n = 0
    sql = f"INSERT OR REPLACE INTO images ({','.join(IMAGE_COLS)}) VALUES ({','.join('?' * len(IMAGE_COLS))})"
    for batch in api.m20_pages(camera=camera, sol_min=sol_min, sol_max=before_sol):
        con.executemany(sql, [[_with_season(r)[c] for c in IMAGE_COLS] for r in batch])
        con.commit()
        n += len(batch)
        if n % 5000 < len(batch):
            print(f"  {n} records, down to sol {batch[-1]['sol']}", file=sys.stderr, flush=True)
    return n


def ingest_route(rover: str) -> int:
    """Store one row per stop (site, drive). The published total distance sometimes steps
    backwards, so the odometer is the running maximum over sols."""
    stops = [p for p in api.waypoints(rover) if isinstance(p.get("sol"), int) and p.get("site") is not None]
    stops.sort(key=lambda p: (p["sol"], p["site"], int(p.get("drive") or 0)))
    con = db.connect()
    odo = 0.0
    rows = []
    for p in stops:
        total = p.get("dist_total_m")
        if isinstance(total, (int, float)):
            odo = max(odo, float(total))
        t = seasons.sol_to_utc(rover, p["sol"] + 0.5)
        rows.append((rover, int(p["site"]), int(p.get("drive") or 0), p["sol"], p.get("lat"), p.get("lon"),
                     p.get("elev_geoid"), odo, total, 1 if str(p.get("final", "y")).lower().startswith("y") else 0,
                     round(seasons.ls(t), 3), seasons.mars_year(t)))
    con.executemany("INSERT OR REPLACE INTO stops VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    r = sub.add_parser("route")
    r.add_argument("--rover", choices=["m20", "msl"], default="m20")
    i = sub.add_parser("images")
    i.add_argument("--rover", choices=["m20"], default="m20")
    i.add_argument("--camera", help="instrument name, e.g. NAVCAM_LEFT, FRONT_HAZCAM_LEFT_A, SKYCAM")
    i.add_argument("--recent", type=int, help="only re-pull this many sols back from the newest stored")
    i.add_argument("--before-sol", type=int, help="only pull sols up to this one (to resume an interrupted pull)")
    i.add_argument("--from-sol", type=int, help="only pull sols from this one on (to split a long pull into ranges)")
    a = ap.parse_args(argv)
    if a.what == "route":
        print(f"{ingest_route(a.rover)} stops stored for {a.rover}")
    else:
        print(f"{ingest_images(a.rover, a.camera, a.recent, a.before_sol, a.from_sol)} image records stored for {a.rover} {a.camera or 'all cameras'}")


if __name__ == "__main__":
    main()
