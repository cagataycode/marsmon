"""Read NASA's public raw-image and route feeds for Perseverance (m20) and Curiosity (msl).

These JSON endpoints power the mars.nasa.gov raw-image pages. They are public but
undocumented, so every record is normalised here and the raw fields we rely on are
listed in one place. Requests are paced so the feeds are not hammered.
"""
import json
import time
import urllib.parse
import urllib.request

M20_IMAGES = "https://mars.nasa.gov/rss/api/"
MSL_IMAGES = "https://mars.nasa.gov/api/v1/raw_image_items/"
WAYPOINTS = "https://mars.nasa.gov/mmgis-maps/{code}/Layers/json/{code}_waypoints.json"
ROUTE_CODES = {"m20": "M20", "msl": "MSL"}
PAGE_SIZE = 100  # the Perseverance feed caps pages at 100
PAUSE_S = 0.25


def get_json(url: str, retries: int = 4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def m20_url(page: int, camera: str | None = None, sol_min: int | None = None, sol_max: int | None = None) -> str:
    q = urllib.parse.urlencode({"feed": "raw_images", "category": "mars2020", "feedtype": "json",
                                "num": PAGE_SIZE, "page": page, "order": "sol desc"})
    if camera:
        q += "&search=%7C" + urllib.parse.quote(camera)
    if sol_min is not None:
        q += f"&condition_2={int(sol_min)}:sol:gte"
    if sol_max is not None:
        q += f"&condition_3={int(sol_max)}:sol:lte"
    return M20_IMAGES + "?" + q


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _dims(s):
    try:
        w, h = s.strip("()").split(",")
        return int(w), int(h)
    except Exception:
        return None, None


def m20_record(im: dict) -> dict:
    """Normalise one Perseverance image record."""
    ext = im.get("extended") or {}
    files = im.get("image_files") or {}
    w, h = _dims(ext.get("dimension"))
    lmst = im.get("date_taken_mars") or ""
    drive = im.get("drive")
    return {
        "rover": "m20",
        "imageid": im["imageid"],
        "sol": im.get("sol"),
        "camera": (im.get("camera") or {}).get("instrument"),
        "taken_utc": im.get("date_taken_utc"),
        "lmst": lmst.split("M", 1)[1] if "M" in lmst else None,
        "received_utc": im.get("date_received"),
        "site": im.get("site"),
        "drive": int(drive) if str(drive).isdigit() else None,
        "width": w,
        "height": h,
        "mast_az": _num(ext.get("mastAz")),
        "mast_el": _num(ext.get("mastEl")),
        "sample_type": im.get("sample_type"),
        "url_small": files.get("small"),
        "url_medium": files.get("medium"),
        "url_large": files.get("large"),
        "url_full": files.get("full_res"),
        "credit": im.get("credit"),
    }


def m20_pages(camera: str | None = None, sol_min: int | None = None, sol_max: int | None = None, max_pages: int | None = None):
    """Yield lists of normalised records, newest sol first, until every result is read.

    The feed sometimes returns an empty page mid-way. That is retried, and if it persists
    it raises instead of being mistaken for the end of the data."""
    page = 0
    total = None
    while max_pages is None or page < max_pages:
        images = []
        for attempt in range(4):
            data = get_json(m20_url(page, camera, sol_min, sol_max))
            total = data.get("total_results", total)
            images = data.get("images") or []
            if images or (total is not None and page * PAGE_SIZE >= total):
                break
            time.sleep(3 * (attempt + 1))
        if not images:
            if total is not None and page * PAGE_SIZE < total:
                raise RuntimeError(f"feed returned no images at page {page} of {total} results; rerun with --before-sol to resume")
            return
        yield [m20_record(im) for im in images]
        page += 1
        time.sleep(PAUSE_S)


def waypoints(rover: str) -> list[dict]:
    """Route stops ('waypoints') published for the rover's traverse map."""
    code = ROUTE_CODES[rover]
    data = get_json(WAYPOINTS.format(code=code))
    return [f.get("properties") or {} for f in data.get("features", [])]
