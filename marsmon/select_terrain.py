"""Pick one terrain image per route stop, for Jev to tag and for hand labelling.

    python3 -m marsmon.select_terrain --rover m20

Rules (all in code, so they can be read and changed):
- the image was taken at the stop's position (same site and drive numbers);
- left Navcam, full 1280x960 frame (not a thumbnail or a horizon strip);
- the camera points down at the ground ahead: mast elevation between -45 and -10 degrees;
- among those, prefer about -25 degrees (near ground and some distance in one frame),
  then a time near local noon (short shadows);
- avoid frames aimed more than 100 degrees off the rover's forward direction when
  another frame exists: looking back and down can show the rover's own deck instead
  of the ground (seen in NLF_1815_0828058476_612ECM_N0871640NCAM02814_07_195J).

Writes data/derived/<rover>_terrain_frames.csv and a review page with thumbnails.
"""
import argparse
import csv
import html
from pathlib import Path

from . import db

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"
EL_MIN, EL_MAX, EL_BEST = -45.0, -10.0, -25.0
FIELDS = ["rover", "site", "drive", "stop_sol", "ls", "mars_year", "elev_m", "odometer_km", "final_stop",
          "candidates", "imageid", "image_sol", "lmst", "mast_el", "mast_az", "url_small", "url_full", "credit"]


def _hours(lmst: str | None) -> float | None:
    try:
        h, m, s = lmst.split(":")
        return int(h) + int(m) / 60 + float(s) / 3600
    except Exception:
        return None


def score(img) -> float:
    """Lower is better."""
    h = _hours(img["lmst"])
    az = img["mast_az"]
    looking_back = az is not None and abs(az) > 100
    return (abs(img["mast_el"] - EL_BEST) + (abs(h - 12.0) * 2 if h is not None else 12)
            + (1000 if looking_back else 0))


def select(rover: str) -> list[dict]:
    con = db.connect()
    stops = con.execute("SELECT * FROM stops WHERE rover=? ORDER BY sol, site, drive", (rover,)).fetchall()
    rows = []
    for st in stops:
        cands = con.execute(
            """SELECT * FROM images WHERE rover=? AND site=? AND drive=? AND camera='NAVCAM_LEFT'
               AND width>=1280 AND height>=960 AND mast_el BETWEEN ? AND ?""",
            (rover, st["site"], st["drive"], EL_MIN, EL_MAX)).fetchall()
        best = min(cands, key=score) if cands else None
        rows.append({
            "rover": rover, "site": st["site"], "drive": st["drive"], "stop_sol": st["sol"],
            "ls": round(st["ls"], 1), "mars_year": st["mars_year"], "elev_m": round(st["elev_m"], 1) if st["elev_m"] is not None else None,
            "odometer_km": round(st["odometer_m"] / 1000, 3), "final_stop": st["final"], "candidates": len(cands),
            "imageid": best["imageid"] if best else None, "image_sol": best["sol"] if best else None,
            "lmst": best["lmst"] if best else None, "mast_el": round(best["mast_el"], 1) if best else None,
            "mast_az": round(best["mast_az"], 1) if best and best["mast_az"] is not None else None,
            "url_small": best["url_small"] if best else None, "url_full": best["url_full"] if best else None,
            "credit": best["credit"] if best else None,
        })
    return rows


def write_csv(rows, path: Path):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def write_review(rows, path: Path, rover: str):
    picked = [r for r in rows if r["imageid"]]
    cards = []
    for r in picked:
        link = f"https://mars.nasa.gov/mars2020/multimedia/raw-images/{html.escape(r['imageid'])}"
        cards.append(
            f'<figure><a href="{link}"><img loading="lazy" src="{html.escape(r["url_small"])}" alt="Navcam image {html.escape(r["imageid"])}"></a>'
            f'<figcaption><b>Sol {r["stop_sol"]}</b> · stop {r["site"]}/{r["drive"]}<br>'
            f'MY{r["mars_year"]} Ls {r["ls"]}° · {r["elev_m"]} m · {r["odometer_km"]} km<br>'
            f'el {r["mast_el"]}° · {r["lmst"][:5] if r["lmst"] else ""} LMST</figcaption></figure>')
    missing = len(rows) - len(picked)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MarsMon terrain frames: {rover}</title>
<style>
:root {{ color-scheme: light dark; --bg:#fbfaf8; --fg:#222; --muted:#6b6b6b; --card:#fff; --line:#e4e1dc; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161514; --fg:#eee; --muted:#a3a3a3; --card:#201f1d; --line:#34322f; }} }}
body {{ margin:0; padding:24px; font:14px/1.45 system-ui, sans-serif; background:var(--bg); color:var(--fg); }}
h1 {{ font-size:20px; margin:0 0 4px; }} p {{ color:var(--muted); margin:0 0 16px; max-width:70ch; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:12px; }}
figure {{ margin:0; background:var(--card); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
img {{ width:100%; aspect-ratio:4/3; object-fit:cover; display:block; background:#000; }}
figcaption {{ padding:8px 10px; font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }}
figcaption b {{ color:var(--fg); }}
</style></head><body>
<h1>Terrain frame per route stop: {"Perseverance" if rover == "m20" else rover}</h1>
<p>{len(picked)} of {len(rows)} stops have a frame that meets the rules in <code>marsmon/select_terrain.py</code>;
{missing} have none. Images: NASA/JPL-Caltech raw images (uncalibrated), shown from NASA's servers. Click a frame for its NASA page.</p>
<div class="grid">{''.join(cards)}</div></body></html>"""
    path.write_text(page)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rover", choices=["m20"], default="m20")
    a = ap.parse_args(argv)
    rows = select(a.rover)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows, OUT_DIR / f"{a.rover}_terrain_frames.csv")
    write_review(rows, OUT_DIR / f"{a.rover}_terrain_review.html", a.rover)
    have = sum(1 for r in rows if r["imageid"])
    print(f"{have} of {len(rows)} stops have a terrain frame")


if __name__ == "__main__":
    main()
