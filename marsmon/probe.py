"""A small Jev probe on terrain frames that are NOT in the hand-label sample.

    python3 -m marsmon.probe select            # choose the probe frames (once; committed)
    python3 -m marsmon.probe dry-run           # build every request without downloading or sending
    python3 -m marsmon.probe send              # download the frames from NASA and ask Jev

`send` saves one file per frame in runs/<timestamp>/ with the request (image replaced
by its size and SHA-256), the response, and Jev's answers in label vocabulary, plus a
summary. Downloaded images are cached in data/images/ (gitignored).
"""
import argparse
import csv
import datetime as dt
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

from . import jev, questions

ROOT = Path(__file__).resolve().parent.parent
FRAMES = ROOT / "data" / "derived" / "m20_terrain_frames.csv"
SAMPLE = ROOT / "data" / "labels" / "terrain_sample.json"
PROBE = ROOT / "data" / "probe" / "terrain_probe_v1.json"
IMAGES = ROOT / "data" / "images"
RUNS = ROOT / "runs"
SEED = 20261126
PER_TENTH = 2
# Hard cases picked on purpose, with the reason. Must not be in the label sample.
HARD_CASES = {
    "NLF_1815_0828058476_612ECM_N0871640NCAM02814_07_195J": "rover deck fills the frame: ground_visible should be no",
    "NLF_1761_0823274598_489ECM_N0831384NCAM03761_01_195J": "open hillside seen looking sideways: steep_slope should be yes",
}


def select() -> dict:
    if PROBE.exists():
        raise SystemExit(f"{PROBE.name} already exists; runs refer to it.")
    labelled = {x["imageid"] for x in json.loads(SAMPLE.read_text())["items"]}
    clash = labelled & set(HARD_CASES)
    if clash:
        raise SystemExit(f"hard cases are in the label sample: {clash}")
    rows = [r for r in csv.DictReader(FRAMES.open()) if r["imageid"] and r["imageid"] not in labelled]
    rows.sort(key=lambda r: float(r["odometer_km"]))
    total = float(rows[-1]["odometer_km"])
    rng = random.Random(SEED)
    picked = []
    for t in range(10):
        stretch = [r for r in rows if min(9, int(float(r["odometer_km"]) / total * 10)) == t and r["imageid"] not in HARD_CASES]
        picked += [(r, "random, tenth %d of the route" % (t + 1)) for r in rng.sample(stretch, PER_TENTH)]
    url = {r["imageid"]: r["url_small"].replace("_320.jpg", "_1200.jpg") for r in rows}
    import sqlite3
    con = sqlite3.connect(ROOT / "data" / "marsmon.sqlite")
    for imageid, why in HARD_CASES.items():
        row = con.execute("SELECT url_large, sol FROM images WHERE imageid=?", (imageid,)).fetchone()
        picked.append(({"imageid": imageid, "image_sol": row[1]}, "hard case: " + why))
        url[imageid] = row[0]
    items = [{"imageid": r["imageid"], "sol": int(r["image_sol"]), "image_url": url[r["imageid"]], "why": why} for r, why in picked]
    probe = {"seed": SEED, "questions_version": questions.VERSION, "excludes": "every frame in data/labels/terrain_sample.json", "items": items}
    PROBE.parent.mkdir(parents=True, exist_ok=True)
    PROBE.write_text(json.dumps(probe, indent=1) + "\n")
    return probe


REVERSED = "main_terrain__reversed"


def add_order_check(payload: dict, record: dict) -> None:
    """Probe-only diagnostic: ask main_terrain a second time with the options in reverse order.
    Jev's docs note that a Choice can favour its first option; if the top answer changes with
    the order, the terrain answer is order-sensitive. Not used for any label."""
    q = payload["questions"]["main_terrain"]
    rev = {"type": "choice", "instructions": q["instructions"], "criteria": dict(reversed(list(q["criteria"].items())))}
    payload["questions"][REVERSED] = rev
    record["questions"][REVERSED] = rev


def fetch(item: dict) -> bytes:
    path = IMAGES / (item["imageid"] + ".jpg")
    if not path.exists():
        IMAGES.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(item["image_url"], timeout=60) as r:
            path.write_bytes(r.read())
        time.sleep(1.0)
    return path.read_bytes()


def dry_run(probe: dict):
    """Build every request with a stand-in image of the right size: checks shape and references."""
    fake = _fake_jpeg(1200, 902)
    payload, record = jev.build_request(fake)
    add_order_check(payload, record)
    refs = list(payload["assets"])
    text = json.dumps({k: v for k, v in payload.items() if k != "assets"})
    assert all(r in text for r in refs), "every asset must be referenced in state or questions"
    assert set(payload["questions"]) == {q["id"] for q in questions.TERRAIN} | {REVERSED}
    print(json.dumps(record, indent=1))
    print(f"\n{len(probe['items'])} frames would be sent, one request each, with {len(payload['questions'])} questions per request.")
    print("Dry run: nothing downloaded or sent.")


def _fake_jpeg(w: int, h: int) -> bytes:
    # Minimal bytes with a JPEG start-of-frame marker, enough for the size check (never sent).
    return b"\xff\xd8\xff\xc0\x00\x11\x08" + h.to_bytes(2, "big") + w.to_bytes(2, "big") + b"\x03" + b"\x00" * 9


def send(probe: dict):
    jev.load_env()
    run = RUNS / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run.mkdir(parents=True)
    summary, tokens = [], 0
    for k, item in enumerate(probe["items"], 1):
        image = fetch(item)
        payload, record = jev.build_request(image)
        add_order_check(payload, record)
        entry = {"imageid": item["imageid"], "why": item["why"], "image_url": item["image_url"], "request": record}
        t0 = time.time()
        try:
            resp = jev.call(payload)
            ans = resp["answers"]
            entry.update(response=resp, seconds=round(time.time() - t0, 2), labels=jev.as_labels(ans),
                         order_check={"forward": ans["main_terrain"]["choice"], "reversed": ans[REVERSED]["choice"]})
            tokens += (resp.get("usage") or {}).get("input_tokens", 0)
        except jev.JevError as e:
            entry.update(error=str(e), seconds=round(time.time() - t0, 2))
        (run / f"{k:02d}_{item['imageid']}.json").write_text(json.dumps(entry, indent=1) + "\n")
        summary.append(entry)
        print(f"{k:2d}/{len(probe['items'])} {item['imageid'][:24]} " + (json.dumps(entry.get("labels")) if "labels" in entry else "ERROR " + entry["error"]), flush=True)
        if "error" in entry and entry["error"].startswith(("401", "403", "0:")):
            print("Stopping: the API refused the key or could not be reached.", file=sys.stderr)
            break
    meta = {"model_requested": jev.MODEL, "models_answered": sorted({e["response"]["model"] for e in summary if "response" in e}),
            "questions_version": questions.VERSION, "frames": len(summary), "errors": sum("error" in e for e in summary),
            "input_tokens_total": tokens,
            "terrain_same_top_choice_both_orders": sum(1 for e in summary if "order_check" in e and e["order_check"]["forward"] == e["order_check"]["reversed"])}
    (run / "summary.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["select", "dry-run", "send"])
    a = ap.parse_args(argv)
    if a.action == "select":
        p = select()
        print(f"{len(p['items'])} probe frames -> {PROBE.relative_to(ROOT)}")
        return
    probe = json.loads(PROBE.read_text())
    dry_run(probe) if a.action == "dry-run" else send(probe)


if __name__ == "__main__":
    main()
