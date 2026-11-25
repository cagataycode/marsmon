"""Choose the frames to label by hand.

    python3 -m marsmon.label_sample --rover m20 --n 150

Splits the route into 10 equal stretches of distance driven and draws the same number
of frames at random from each, so every part of the journey (and the seasons it
crossed) is covered. The draw uses a fixed seed and the result is committed, so the
sample can be checked and reproduced. Frames are shown in shuffled order, so the
labeller doesn't walk the route in sequence.

Refuses to overwrite an existing sample unless --force is given, because labels refer
to it.
"""
import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMES_DIR = ROOT / "data" / "derived"
OUT = ROOT / "data" / "labels" / "terrain_sample.json"
SEED = 20261125
STRETCHES = 10


def build(rover: str, n: int) -> dict:
    rows = [r for r in csv.DictReader((FRAMES_DIR / f"{rover}_terrain_frames.csv").open()) if r["imageid"]]
    rows.sort(key=lambda r: float(r["odometer_km"]))
    total = float(rows[-1]["odometer_km"]) or 1.0
    bins = [[] for _ in range(STRETCHES)]
    for r in rows:
        bins[min(STRETCHES - 1, int(float(r["odometer_km"]) / total * STRETCHES))].append(r)
    rng = random.Random(SEED)
    per = n // STRETCHES
    picked = []
    for b in bins:
        picked += rng.sample(b, min(per, len(b)))
    rest = [r for r in rows if r not in picked]  # top up if a stretch had too few frames
    picked += rng.sample(rest, max(0, n - len(picked)))
    rng.shuffle(picked)
    items = [{
        "imageid": r["imageid"],
        "image_url": r["url_small"].replace("_320.jpg", "_1200.jpg"),
        "nasa_page": f"https://mars.nasa.gov/mars2020/multimedia/raw-images/{r['imageid']}",
        "stop": f"{r['site']}_{r['drive']}",
        "sol": int(r["image_sol"]),
        "ls": float(r["ls"]),
        "mars_year": int(r["mars_year"]),
        "elev_m": float(r["elev_m"]),
        "odometer_km": float(r["odometer_km"]),
    } for r in picked]
    return {"rover": rover, "seed": SEED, "stretches": STRETCHES, "from_frames": len(rows), "items": items}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rover", choices=["m20"], default="m20")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--force", action="store_true", help="replace an existing sample (labels refer to it)")
    a = ap.parse_args(argv)
    if OUT.exists() and not a.force:
        raise SystemExit(f"{OUT.name} already exists; labels refer to it. Use --force only if you mean to replace it.")
    sample = build(a.rover, a.n)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sample, indent=1) + "\n")
    print(f"{len(sample['items'])} frames sampled from {sample['from_frames']} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
