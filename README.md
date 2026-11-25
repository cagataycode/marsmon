# MarsMon

**MarsMon is a field report on the Mars rovers, built from NASA's public raw images.** The report covers what the rover did each sol, what ground it crossed, and the season on Mars. A small vision model (TypeSafe's Jev) answers typed questions about the pictures. Plain code does every number and decision. An LLM (Claude) writes a short weekly report from those computed tables.

> **Status: early build (Nov 2026).** The data feeds are checked and the route and image metadata ingest works. Nothing has been sent to Jev yet. Every step so far, including dead ends and null results, is in [`docs/LOG.md`](docs/LOG.md).

## Why Mars rovers

- **New data every day:** Perseverance has about 1.05 million raw images, Curiosity about 1.5 million. Both feeds update within a day or two of the images being taken.
- **Route data:** every stop of both rovers, with position, elevation and distance driven.
- **Measured dust and cloud data from the rovers' own instruments,** which the image-based judgments can be checked against.

The full reasoning, the draft Jev questions and the truth tables are in [`docs/CONCEPT.md`](docs/CONCEPT.md).

## How the work is split

| Part | Does | Doesn't |
|---|---|---|
| **Code** | Fetches feeds, computes Mars seasons, cleans the odometer, picks which images to ask about, turns answers into labels using truth tables, does all statistics | Judge what is in a picture |
| **Jev** | Answers one typed question per judgment about a single image: "Is the arm touching a rock?", "Which terrain is this?" | Count, do arithmetic, or make the final decision |
| **Claude** | Writes the weekly report from computed tables, citing sol and image ID for each claim | Invent numbers or interpret geology beyond the tags |
| **Hand labels** | A labelled sample by the author, used to measure how often Jev is right | — |

## Transparency

- **The work is logged as it happens.** [`docs/LOG.md`](docs/LOG.md) records each finding, decision and dead end with the image IDs behind it, so any claim can be checked on NASA's site.
- **AI assistance is disclosed.** Code and analysis are written by the author together with Claude Code (Anthropic's coding assistant). Commits made that way carry a `Co-Authored-By: Claude` line.
- **Jev requests will be logged and reproducible.** Question wording will live in one file, and every request payload will be saved so results can be rerun.
- **Exploration scripts are kept as they were run.** `probes/` holds the scripts from the first data check, unchanged, so the numbers in the log can be reproduced.

## Run it

Python 3.10+ and the standard library only.

```bash
python3 -m marsmon.ingest route --rover m20                 # route stops (also: --rover msl)
python3 -m marsmon.ingest images --rover m20 --camera NAVCAM_LEFT
python3 -m marsmon.select_terrain --rover m20                # one terrain frame per stop
python3 -m unittest discover tests
```

The local database (`data/marsmon.sqlite`) is rebuilt from the feeds and not committed. Small derived tables in `data/derived/` are committed.

## Data and credits

- **Raw images:** NASA/JPL-Caltech; SkyCam images NASA/JPL-Caltech/CAB. These are uncalibrated raw images from the [Perseverance](https://mars.nasa.gov/mars2020/multimedia/raw-images/) and [Curiosity](https://mars.nasa.gov/msl/multimedia/raw-images/) raw-image pages. The JSON feeds behind those pages are public but undocumented.
- **Route stops:** the waypoint files behind NASA's rover traverse maps.
- **Planned reference data:**
  - M. Smith, *Perseverance MEDA/TIRS dust and water ice retrievals*, Mendeley Data (CC BY 4.0).
  - M. Lemmon, *The Perseverance Rover's Mastcam-Z Visible Aerosol Optical Depth Record*, v2, Mendeley Data (CC BY 4.0).
- **Mars seasons:** Allison & McEwen (2000) algorithm, as used in NASA GISS Mars24. Mars Year numbering follows Clancy et al. (2000).
