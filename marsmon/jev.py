"""Ask TypeSafe's Jev the questions in marsmon/questions.py about one image.

Request shape (docs.typesafe.ai, images and HTTP API pages):
    POST https://api.typesafe.ai/v1/systemone
    headers: Authorization: Bearer <key>, TypeSafe-Danger-Zone-Images: true
    {"model": ..., "state": {"photo": <ref>}, "questions": {...},
     "assets": {<ref>: {"type": "image", "format": "jpg", "data_base64": ...}}}

The key is read from the TYPESAFE_API_KEY environment variable or from marsmon/.env
(gitignored). A failed call raises JevError; it is never turned into an answer.
"""
import base64
import hashlib
import json
import os
import struct
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from . import questions

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
ROOT = Path(__file__).resolve().parent.parent

# Noul reading (TypeSafe's suggested starting thresholds): above YES = yes, below NO = no, between = unsettled.
YES, NO = 0.7, 0.3

# Image limits from the docs; images are rejected, never resized.
MIN_SIDE, MAX_SIDE = 280, 1568
MIN_PIXELS, MAX_PIXELS = 78_400, 2_458_624


class JevError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}")
        self.status = status


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def jpeg_size(data: bytes) -> tuple[int, int]:
    """Width and height from a JPEG's start-of-frame marker."""
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        seg = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg
    raise ValueError("no JPEG size marker found")


def check_image(data: bytes) -> tuple[int, int]:
    w, h = jpeg_size(data)
    if not (MIN_SIDE <= w <= MAX_SIDE and MIN_SIDE <= h <= MAX_SIDE and MIN_PIXELS <= w * h <= MAX_PIXELS):
        raise ValueError(f"{w}x{h} is outside Jev's image limits")
    return w, h


def jev_questions(qs=questions.TERRAIN) -> dict:
    """Translate the shared question definitions into the API's question objects."""
    out = {}
    for q in qs:
        if q["kind"] == "noul":
            out[q["id"]] = {"type": "noul", "instructions": q["text"],
                            "criteria": {"true": q["true"], "false": q["false"]}}
        elif q["kind"] == "choice":
            out[q["id"]] = {"type": "choice", "instructions": q["text"], "criteria": dict(q["options"])}
        else:
            raise ValueError(f"unknown question kind {q['kind']}")
    return out


def build_request(image: bytes) -> tuple[dict, dict]:
    """Return (payload to send, record to log). The log keeps a hash instead of the image bytes."""
    ref = f"{uuid.uuid4()}-photo"
    w, h = check_image(image)
    payload = {
        "model": MODEL,
        "state": {"photo": ref},
        "questions": jev_questions(),
        "assets": {ref: {"type": "image", "format": "jpg", "data_base64": base64.b64encode(image).decode()}},
    }
    record = {**payload, "assets": {ref: {"type": "image", "format": "jpg", "width": w, "height": h, "bytes": len(image),
                                          "sha256": hashlib.sha256(image).hexdigest()}}}
    return payload, record


def call(payload: dict, timeout: int = 90) -> dict:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise JevError(0, "TYPESAFE_API_KEY is not set. Put it in marsmon/.env (gitignored).")
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "TypeSafe-Danger-Zone-Images": "true"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise JevError(e.code, e.read().decode(errors="replace")[:400]) from None
    except urllib.error.URLError as e:
        raise JevError(0, f"could not reach TypeSafe: {e.reason}") from None


def reading(p: float) -> str:
    return "yes" if p > YES else "no" if p < NO else "unsettled"


def as_labels(answers: dict) -> dict:
    """Turn Jev's probabilities into the same answer vocabulary the hand labels use.
    Same rule as the labelling page: when there is no ground, the other questions are n/a."""
    out = {}
    ground = reading(answers["ground_visible"]["noul"])
    out["ground_visible"] = {"yes": "yes", "no": "no", "unsettled": "unsure"}[ground]
    for q in questions.TERRAIN:
        if q["id"] == "ground_visible":
            continue
        if ground == "no" and q["id"] in questions.NEEDS_GROUND:
            out[q["id"]] = "n/a"
        elif q["kind"] == "noul":
            out[q["id"]] = {"yes": "yes", "no": "no", "unsettled": "unsure"}[reading(answers[q["id"]]["noul"])]
        else:
            out[q["id"]] = answers[q["id"]]["choice"]
    return out
