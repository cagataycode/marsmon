"""Local page for hand-labelling terrain frames.

    python3 -m marsmon.label_server            # then open http://127.0.0.1:8765

It shows one frame at a time with the questions from marsmon/questions.py, and saves
each answer to data/labels/terrain_labels.json as soon as it is given. That file is
written only here, one entry at a time; no other script overwrites it. The page shows
no Jev or Claude answers, so the labels stay blind.

Images load from NASA's servers, so the page needs an internet connection.
"""
import argparse
import datetime as dt
import http.server
import json
import os
import threading
from pathlib import Path

from . import questions

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLE = ROOT / "data" / "labels" / "terrain_sample.json"
DEFAULT_LABELS = ROOT / "data" / "labels" / "terrain_labels.json"
PAGE = Path(__file__).resolve().parent / "label_page.html"


class Store:
    def __init__(self, sample_path: Path, labels_path: Path):
        self.sample = json.loads(sample_path.read_text())
        self.ids = {item["imageid"] for item in self.sample["items"]}
        self.labels_path = labels_path
        self.lock = threading.Lock()

    def labels(self) -> dict:
        if self.labels_path.exists():
            return json.loads(self.labels_path.read_text())
        return {}

    def save(self, imageid: str, answers: dict, note: str) -> dict:
        if imageid not in self.ids:
            raise ValueError("image is not in the sample")
        by_id = {q["id"]: q for q in questions.TERRAIN}
        if set(answers) != set(by_id):
            raise ValueError("every question needs an answer")
        ground = answers["ground_visible"]
        for qid, value in answers.items():
            if qid in questions.NEEDS_GROUND and ground == "no":
                if value != "n/a":
                    raise ValueError(f"{qid} must be n/a when no ground is visible")
            elif value not in questions.allowed_answers(by_id[qid]):
                raise ValueError(f"{qid}: '{value}' is not an allowed answer")
        entry = {
            "answers": answers,
            "note": note.strip()[:500],
            "labelled_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "labeller": "author",
            "questions_version": questions.VERSION,
        }
        with self.lock:
            labels = self.labels()
            labels[imageid] = entry
            self.labels_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.labels_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(labels, indent=1, sort_keys=True) + "\n")
            os.replace(tmp, self.labels_path)  # atomic: never a half-written file
        return entry


def make_handler(store: Store):
    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj).encode(), "application/json")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/api/state":
                self._json(200, {"sample": store.sample, "questions": questions.TERRAIN,
                                 "needs_ground": sorted(questions.NEEDS_GROUND),
                                 "version": questions.VERSION, "labels": store.labels()})
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if self.path != "/api/label":
                return self._send(404, b"not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(min(n, 20000)))
                entry = store.save(body["imageid"], body["answers"], body.get("note", ""))
                self._json(200, {"ok": True, "entry": entry})
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
                self._json(400, {"ok": False, "error": str(e)})

        def log_message(self, fmt, *args):  # keep the terminal quiet
            pass

    return Handler


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    ap.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="where answers are saved")
    a = ap.parse_args(argv)
    store = Store(a.sample, a.labels)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(store))
    print(f"Labelling {len(store.ids)} frames -> {a.labels}")
    print(f"Open http://127.0.0.1:{a.port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
