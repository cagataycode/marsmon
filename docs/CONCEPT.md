# MarsMon: concept (working name)

**MarsMon turns the Mars rovers' daily raw images into a field report.** The report covers what the rover did, what ground it crossed, and what the season was like. Jev makes the judgments about the pictures. Code does every number and every decision. Claude writes a weekly report from what code computed.

Status: concept, written 25 Nov 2026. The numbers below come from live queries made that day. The exploration scripts that produced them are in `probes/`; the findings and decisions are logged in `docs/LOG.md`.

---

## 1. What the data check found

| Source | What we confirmed | Why it matters |
|---|---|---|
| Perseverance raw-image API | 1,055,871 images (579,521 full frames). Filterable by camera and by sol. Each record has local solar time, camera pointing (mast elevation) and a credit line. Sky frames usually arrive a day after they're taken. | Fresh data every day, so real monitoring is possible |
| Curiosity raw-image API | 1,523,172 images; the newest is from 24 Nov 2026 | A second site (Gale crater) to compare with Jezero |
| Perseverance SkyCam | 4,592 frames on 1,845 of 2,032 sols, no gap over 20 sols, all 1056×1024 px | Covers three full Mars years (MY36–38); every 30° season has at least 45 frames |
| Route files (waypoints + traverse JSON) | Perseverance: 708 stops, 45.25 km, elevation −2,570 m → −1,936 m. Curiosity: 1,391 stops, 38.67 km, −4,501 m → −3,469 m. Each stop has sol, lat/lon, tilt and a panorama | Map, elevation profile and distance per sol with no extra work. The odometer field steps backwards 129 times for Perseverance, so code takes a running maximum |
| Curiosity REMS weather feed | 4,745 sols with Ls; latest entry is sol 4995 (Aug 2026) | Season labels and temperature/pressure for Gale |
| Perseverance MEDA public weather feed | Stopped updating in April 2024 (sol 1127) | Can't be used; use the published datasets below instead |
| MEDA/TIRS dust + water-ice optical depth (Smith, CC BY 4.0) | Per observation, MY36–37. Dust and ice separated | Measured haze and cloud data |
| Mastcam-Z aerosol optical depth record (Lemmon, v2 Apr 2026, CC BY 4.0) | Four wavelengths at Jezero; sol coverage not yet checked | Measured haze that may run later in time |
| Dust climatology (Montabone, LMD) | Gridded daily dust maps MY24–36 | Context at regional scale |

**Mars season maths:** `marsmon/seasons.py` (first drafted as `probes/ls.py`) computes Ls and the Mars Year from UTC. It matched Curiosity's published Ls to a median of 0.8° (max 1.6°) over 300 sols, and lands exactly on known year boundaries (MY37 starts 26 Dec 2022, MY38 on 12 Nov 2024, MY39 on 30 Sep 2026).

**Image volume:** Perseverance produces a steady ~23–37k full frames per 100 sols. Curiosity has gone from ~45k to ~70–90k images per 200 sols in later years. SkyCam frames dropped from ~280 to ~170 per 100 sols after sol 1200. That drop is a change in how the rover is operated, not a weather signal; the dashboard should explain it rather than hide it.

## 2. What the raw images look like, and what that means for Jev

The rule is the "human test": a smart non-expert should be able to answer the question at a glance from the image. I looked at examples of each image type.

| Image type | What you see | Jev today? |
|---|---|---|
| Front Hazcam (fisheye, ground level) | Arm and turret, rocks, rover shadow, wheel, horizon hills. Very readable | **Yes** |
| Navcam ground and terrain views | Rocks, layered outcrops, sand, slopes | **Yes** |
| Navcam horizon strips (1280×352, some 1280×256) | Readable, but **what's in view changes**. Sol 795 (clear season) shows the far crater rim through light haze; sol 1155 (dusty season) has a nearby slope filling most of the frame. "How hazy?" would partly be judging the terrain | **Experiment only.** The 256-px strips also need padding to Jev's 280 px minimum |
| SkyCam | Sky seen through a ringed window; low contrast, dust specks on the glass. Clouds are not visible by eye in a raw frame | **Not yet**: code must first stretch the contrast or subtract frames |
| Navcam zenith frames | Sun glare and an almost uniform sky | **Not yet**: phase 2 |

**What this means for the design:** Jev's job is **what's in the pictures**: ground, rocks, the arm, tracks. The **sky and season** panel uses the measured optical depth (code). Haze and clouds judged from images become later experiments, checked against those instruments.

## 3. The dashboard: three panels and a report

1. **The journey.** Map and elevation profile, with terrain tags at each stop. For example, how the ground changed as Perseverance went from the crater floor, over the delta, and up the rim (+530 m between sols ~1000 and 1300). Curiosity's 1 km climb up Mount Sharp is shown alongside.
2. **The rover's day.** A timeline of sols labelled by activity: drive, sampling, close-up science, imaging, pause. The labels come from the camera mix (code), the drive distance (route file) and a few Jev judgments on Hazcam frames. Solar conjunctions (Oct 2021, Nov 2023, Jan 2026) should show up as pauses, which is a free sanity check.
3. **Sky and seasons.** Measured dust and water-ice optical depth by sol, with a Mars-season band underneath. MY36, MY37 and MY38 are drawn on the same season axis. All of it is code.
4. **Weekly field report (Claude).** It's written from the tables, links to the image IDs behind every claim, and compares each week with the same season one Mars year earlier.

## 4. Insight questions, fixed before looking at the results

| # | Question | Already known? | How it's checked |
|---|---|---|---|
| Q1 | How does the terrain change along the route and with elevation, for each rover? | The geology is in mission papers, but not as a tagged series | Your hand labels on a sample |
| Q2 | How does each rover spend its sols, and did that change during big phases (rim climb, sampling campaigns)? | Not published in this form | Camera mix and route file (code); Jev for arm work |
| Q3 | Does the season change how much the rovers drive? | — | Route file (code). **First result below** |
| Q4 | How do the dust and cloud seasons differ from year to year at Jezero, and between Jezero and Gale? | Partly | Optical depth records |
| Q5 | Experiment: can Jev read haze from horizon views where the far rim is in frame, and does that track the optical depth? | No | TIRS and Mastcam-Z optical depth |
| Q6 (phase 2) | Clouds and dust devils in processed sky and horizon frames | Seasonal patterns known | TIRS water-ice optical depth, published dust-devil counts |

**First result (Q3), from the route files alone:** metres driven per sol by northern-hemisphere season.

| Rover / Mars Year | Spring | Summer | Autumn | Winter |
|---|---|---|---|---|
| Perseverance MY37 | 26.3 | 26.8 | 22.0 | 26.5 |
| Perseverance MY38 | 21.0 | 22.6 | 18.9 | 22.0 |
| Curiosity MY36 | 10.0 | 5.5 | 7.0 | 6.0 |
| Curiosity MY37 | 5.6 | 4.8 | 5.9 | 6.0 |
| Curiosity MY38 | 10.7 | 6.3 | 5.3 | 7.9 |

So far there is **no clear seasonal effect**. Driving seems to follow the science plan, not the weather; both rovers run on nuclear power, not solar. Perseverance's autumn dip of ~15% shows up in both years, but it's too small to claim without more checks. This is the kind of honest null result the dashboard and Claude's report must be able to say.

**Where the new value is:** the tagged, continuously updated index, the comparisons (year vs year, rover vs rover, terrain vs elevation), and the rover diary. The seasonal patterns themselves are known science, and the dashboard says so.

## 5. Draft Jev questions

All wording lives in one file (`questions.py`). Each question asks for one judgment. Every Choice gets a Noul alongside it for the case where nothing fits.

**Hazcam frame**
- Noul `arm_at_target`: "Is the rover's robotic arm turret touching or just above a rock or the ground in `photo`?" (false = the arm is stowed or out of frame)
- Noul `wheel_tracks`: "Are wheel tracks visible on the ground in `photo`?"
- Noul `abrasion_patch`: "Is there a round, ground-down patch on a rock in `photo`?"

**Terrain (Navcam / Hazcam at each stop)**
- Noul `ground_visible`: "Is the ground visible in `photo`?" (handles the case where nothing fits)
- Choice `main_terrain`: `layered_outcrop`, `sand_ripples`, `scattered_boulders`, `flat_bedrock`, `loose_pebbles`. Each option is described as a situation.
- Noul `layering`: "Does `photo` show rock in visible layers or bands?"
- Noul `steep_slope`: "Is the rover looking at or standing on a steep slope in `photo`?"

**Experiment (Q5), horizon strips only:**
- Noul `far_rim_in_view`: "Is a distant ridge visible behind the nearby ground in `photo`?" Code only asks about haze when this is a clear yes.
- Score `haze`, with levels described as situations:
  1. "The distant ridge is sharp."
  2. "The distant ridge is visible but soft-edged."
  3. "The distant ridge is barely visible."

**Phase 2 (processed frames):** `clouds_visible`, `dust_column` (dust devil).

## 6. Decisions in code (truth tables)

Example: the label for each sol.

| Drive > 0 m (route file) | CacheCam frames | `arm_at_target` (any frame) | Label |
|---|---|---|---|
| yes | any | any | drive sol (+ secondary label if the arm was used) |
| no | yes | any | sampling sol |
| no | no | ≥ 0.7 | close-up science sol |
| no | no | 0.3–0.7 | unclear (shown as such) |
| no | no | < 0.3 | remote imaging / rest sol |
| no images at all | — | — | pause (conjunction or downlink gap) |

Terrain per stop: code takes the top `main_terrain` option only when `ground_visible` ≥ 0.7. It keeps the full probabilities so the map can show mixed ground.

## 7. Checking Jev (supporting, not the main focus)

- **Hand labels:** ~150 images, spread across camera, season, terrain and both rovers, labelled by hand by the author. They live in a file that scripts never overwrite.
- **Sanity checks without labels:** `wheel_tracks` vs the drive distance from the route file; `abrasion_patch` vs sols with abrasion-tool or SHERLOC/WATSON images.
- **Q5 experiment:** the `haze` score vs TIRS/Mastcam-Z optical depth, using only frames where the far rim is in view.

## 8. Claude's role and its guardrails

- Input: the week's computed tables plus 3–6 example image IDs chosen by code.
- Every number in the report must come from the tables. Every claim cites a sol and an image ID.
- It says "not enough data" or "no clear effect" when that's what the tables show, as in Q3.
- No geology beyond the tags: it says "layered rock", not "lake sediments".
- Each week is compared with the same Ls in the previous Mars year.

## 9. Pipeline

1. **Ingest (daily):** image metadata for both rovers, plus the route files, into SQLite; add Ls and the Mars Year; clean up the odometer.
2. **Select:** about 20–40 images per sol go to Jev, not 300. That means the first frame of each Hazcam sequence, one or two terrain frames per stop, and horizon strips for the experiment.
3. **Prepare:** resize to ≤ 1568 px and pad strips to ≥ 280 px; in phase 2, stretch or subtract the sky frames.
4. **Ask Jev:** bundle each image's questions into one request, and log every payload.
5. **Decide:** truth tables and aggregates by season and stop, in code.
6. **Report:** dashboard and weekly Claude report.

## 10. First slice (MVP)

**Perseverance, the journey panel and the sol timeline:**
- Terrain tags for one Navcam frame per stop (708 stops) plus Hazcam arm/track questions for recent sols, checked against hand labels.
- Sol labels from the camera mix and route file first; Jev's `arm_at_target` added on top.
- The sky and seasons band from the TIRS optical-depth file (code only).
- One weekly Claude report for the current week.

Once that runs, add Curiosity, then the Q5 haze experiment, then processed sky frames.

## 11. Risks and open questions

- **Horizon haze is confounded by what's in view.** That's why it's an experiment with a `far_rim_in_view` gate, not the MVP.
- **Clouds and dust devils need processed frames.** Raw single frames fail the human test.
- **Jev's image input is still marked not production-ready**, and its token count per image is unknown. Measure both in the first probe.
- **The raw-image API is undocumented** and could change; the route odometer has resets. Cache the metadata, clean it in code, and keep the payloads.
- **Coverage of the Mastcam-Z optical-depth file is not yet checked,** and the TIRS file stops at MY37.
- **Credit lines** (NASA/JPL-Caltech, and CAB for MEDA) must be shown next to the images.

## Sources

- Raw images: [Perseverance](https://mars.nasa.gov/mars2020/multimedia/raw-images/), [Curiosity](https://mars.nasa.gov/msl/multimedia/raw-images/)
- Route files: `mars.nasa.gov/mmgis-maps/{M20,MSL}/Layers/json/*_waypoints.json`
- [MEDA PDS page](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html)
- [MEDA/TIRS dust & ice (Smith)](https://data.mendeley.com/datasets/jb26sh4j57/1)
- [Mastcam-Z optical depth (Lemmon)](https://data.mendeley.com/datasets/gktjp9jptb/2)
- [LMD dust climatology](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/), [EPSC-DPS2025-1765](https://meetingorganizer.copernicus.org/EPSC-DPS2025/EPSC-DPS2025-1765.html)
- [Dust devils at Jezero (Nature Geoscience 2022)](https://link.springer.com/article/10.1038/s41561-022-01084-0)
- [Cloudy sols (NASA)](https://science.nasa.gov/blogs/cloudy-sols-are-here-again)
- [Perseverance distance record (Oct 2026)](https://science.nasa.gov/blogs/perseverance-mars-rover/2026/10/12/nasas-perseverance-sets-off-world-record-for-total-distance-driven/)
- Jev limits: [images](https://docs.typesafe.ai/go/images.md), [jaggedness](https://docs.typesafe.ai/go/jaggedness.md)
