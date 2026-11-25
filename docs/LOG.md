# Work log

Newest entries at the bottom. Each entry gives what was checked, what was found, and what was decided. Image IDs can be pasted into NASA's raw-image pages to see the same frames.

---

## 2026-11-25: From a Moon idea to Mars

**Started from:** a Moon monitoring dashboard built on open data.

**Set aside because:** the Moon barely changes on human timescales. Phase and distance are calculated, not observed. Real change (new craters, impact flashes) arrives in monthly or quarterly batches, and expert teams have already studied it closely.

**Compared five space directions:**
- Mars rover images
- space weather forecasts vs what actually happened
- JWST observing programs
- the Deep Space Network live feed
- asteroid alerts

Mars rover images fit best: data arrives daily, there are pictures a person can judge at a glance, and the rovers' instruments provide measurements to check against.

## 2026-11-25: Data check

Live queries, made with the scripts in `probes/`:

- **Perseverance raw-image feed:** 1,055,871 images (579,521 in the default full-frame view).
  - Filterable by camera and sol.
  - Records include local solar time, mast pointing, site/drive position and a credit line.
- **Curiosity raw-image feed:** 1,523,172 images; the newest was taken on 24 Nov 2026.
- **Perseverance SkyCam:** 4,592 frames on 1,845 of 2,032 sols, with no gap over 20 sols, all 1056×1024.
  - Median of 1 day from taken to received.
  - Taken mostly 06–09 h and 13–17 h local time.
- **Route files:**
  - Perseverance: 708 stops, 45.25 km, elevation −2,570 → −1,936 m.
  - Curiosity: 1,391 stops, 38.67 km, −4,501 → −3,469 m.
  - Perseverance's published total distance steps backwards 129 times, so code uses a running maximum.
- **Weather feeds:**
  - Curiosity's REMS feed has 4,745 sols with Ls; the latest is sol 4995.
  - Perseverance's public MEDA weather feed stopped in April 2024 (sol 1127), so it isn't used.
- **Image volume per 100 sols:** Perseverance is steady at about 23–37k full frames. SkyCam frames per 100 sols dropped from about 280 to about 170 after sol 1200. That is an operations change, not weather.
- **Mars-season calculation:**
  - Matches Curiosity's published Ls to a median of 0.8° (max 1.6°) over 300 sols.
  - Hits the MY37, MY38 and MY39 start dates.
- **SkyCam coverage:** MY36, MY37 and MY38 are complete, with every 30° Ls bin holding at least 45 frames.

## 2026-11-25: What the raw images look like

| Frame | What it shows | Meaning for Jev |
|---|---|---|
| `WSM_0882_0745223675_000ECM_N0430000MEDA00000_0000LUJ` (SkyCam, cloud season) | Sky through a ringed window; low contrast; dust specks | Clouds can't be seen by eye in a raw frame |
| `WSM_1118_0766202351_000ECM_N0514014MEDA00000_0000LUJ` (SkyCam, dust season) | Same view, with a dark clump on the window ring | Same |
| `NLF_0898_0746644587_131ECM_N0440830NCAM00501_01_295J` (Navcam pointed at 88°) | Sun glare and an almost uniform sky | Clouds need frames subtracted from each other |
| `FLF_2023_0846549745_302ECM_N0930000FHAZ00206_01_295J` (Front Hazcam) | Arm and turret, rocks, rover shadow, hills | Easy to judge at a glance |
| `NLG_0795_0737509237_987ECM_N0391036NCAM00500_00_2I4J` (Navcam strip, clear season) | Far crater rim visible through light haze | Haze readable |
| `NLG_1155_0769483170_880ECM_N0522644NCAM00500_00_2I4J` (Navcam strip, dusty season) | A nearby slope fills most of the frame | Haze would partly be judging the terrain |

**Decision:**
- Jev's first job is what is on the ground: terrain, arm, tracks.
- The sky and season panel uses measured optical depth (code only).
- Haze from horizon strips becomes a gated experiment, asked only when a distant ridge is in view.
- Clouds and dust devils wait until code can prepare processed frames.

## 2026-11-25: First insight test: does the season change how much the rovers drive?

Metres driven per sol by northern-hemisphere season, from the route files alone:

| Rover / Mars Year | Spring | Summer | Autumn | Winter |
|---|---|---|---|---|
| Perseverance MY37 | 26.3 | 26.8 | 22.0 | 26.5 |
| Perseverance MY38 | 21.0 | 22.6 | 18.9 | 22.0 |
| Curiosity MY36 | 10.0 | 5.5 | 7.0 | 6.0 |
| Curiosity MY37 | 5.6 | 4.8 | 5.9 | 6.0 |
| Curiosity MY38 | 10.7 | 6.3 | 5.3 | 7.9 |

**Result: no clear seasonal effect.** Driving follows the science plan; both rovers run on nuclear power, not solar. Perseverance's autumn dip of about 15% appears in both years, but it's too small to claim without more checks. The first version of this calculation summed positive steps of the published odometer, which double-counts after its backward steps and gave impossible values (over 1 km per sol). The cleaned odometer fixes that.

## 2026-11-25: Repository and first ingest

- **Code:**
  - `marsmon/seasons.py` covers Ls, Mars Year and the sol clock. The tests check the year starts, the landing seasons, and the sol clock against two real frames to within 30 minutes.
  - `marsmon/api.py` holds the feed readers.
  - `marsmon/ingest.py` writes route stops and image metadata into SQLite.
- **Route stops stored:** Perseverance 708 (554 marked as the end of a drive), Curiosity 1,391.
- **Bug found and fixed:** the first full Navcam pull stopped silently after 14,000 of 64,795 records (sols 1548–2024). The feed had returned one empty page, and the reader took that as the end. It now retries, and raises an error if a page is still empty before the stated total is reached. A `--before-sol` option resumes an interrupted pull.
- **Navcam frame sizes:** full frames come in several sizes (1288×968, 1296×976, 1280×960 and others). Strips are 1280×256 or 1280×352. The picker treats anything at least 1280×960 as a full frame.
- **Terrain picker, first run on sols 1548–2024:** 140 of 143 stops have a full Navcam frame pointed 10–45° below the horizon at the same site/drive.
- **Four picks checked by eye:**
  - `NLF_1541_0803730756_507EBY_N0752358SCAM01541_00_0LLJ`: flat pebbly ground.
  - `NLF_1556_0805075831_506ECM_N0770942NCAM03556_07_195J`: sand ripples and one rock.
  - `NLF_2010_0845370078_987ECM_N0920000NCAM13009_01_195J`: a rocky slope with sky.
  - `NLF_2023_0846524621_762EBY_N0930000SCAM01023_00_0LLJ`: scattered loose rocks.

  All four are readable terrain. Pointing at about −25° shows ground texture well, but outcrops further away less so. That trade-off should be checked with the hand labels.

## 2026-11-25: Hand-labelling page

- **One source of wording:** `marsmon/questions.py` holds every question (version `terrain-v1`). The labelling page reads its definitions from there, and the Jev requests will too, so a person and the model see the same criteria. Four questions:
  - `ground_visible` (Noul): the null case, e.g. frames of sky or rover hardware.
  - `main_terrain` (Choice of five).
  - `layering` (Noul).
  - `steep_slope` (Noul).
- **Labels stay blind:** the page shows only the frame, with no sol, place, season, Jev answer or Claude suggestion. Each answer goes to `data/labels/terrain_labels.json`, which only the page's server writes, one entry at a time.
- **Sample:** `marsmon/label_sample.py` splits the route into 10 equal stretches of distance and draws 15 frames from each with a fixed seed. Frames are shown shuffled. The sample file is committed and the script refuses to overwrite it.
- **Testing on a 20-frame scratch sample found two problems:**
  - **Fast typing landed on the wrong frame.** Keys pressed while a save was in flight went to the previous frame. The page now moves on at once and goes back with an error if the save fails.
  - **One picked frame showed the rover's deck, not the ground.** Frame `NLF_1815_0828058476_612ECM_N0871640NCAM02814_07_195J`, mast azimuth −122°, elevation −25°. The picker now avoids frames aimed more than 100° off the rover's forward direction when another frame exists at that stop. Another frame at +118° showed open hillside, so azimuth alone isn't a clean rule. The `ground_visible` labels will show how often deck frames still slip through.

## 2026-11-25: Complete Navcam metadata, terrain frames and the label sample

- **Running three pulls in parallel got us refused.** I split the remaining sols (0–595) into three ranges and pulled them at once. NASA's feed then answered HTTP 403 for a few minutes, and all three pulls stopped. After that:
  - The reader now waits about one second between requests and runs one pull at a time.
  - On 403 or 429 it stops with a clear message instead of retrying.
  - Ranges are only for resuming, not for parallel pulls.
- **Counts were checked against the feed:** stored counts compared with the feed's own total for every 200-sol range.
  - The interrupted ranges were short by 2, 86 and 91 records. The cause is likely the feed's paging: results are only ordered by sol, so pages can shift between requests.
  - Re-pulling sols 0–599 one range at a time fixed it. **64,795 of 64,795** left-Navcam records are stored, and every 200-sol range matches.
- **Terrain frames:** 682 of 708 route stops have a frame, including 553 of the 554 end-of-drive stops. 10 picked frames are still aimed more than 100° off forward, because no other frame existed at those stops.
  - Frames per tenth of the route: 99, 26, 82, 60, 61, 80, 86, 56, 54, 78.
  - The second tenth is thin because the rover drove long distances with few stops there.
  - Table: `data/derived/m20_terrain_frames.csv`. Thumbnails: `data/derived/m20_terrain_review.html`, which loads images from NASA.
- **Label sample:** 150 frames, 15 from each tenth, seed 20261125, in `data/labels/terrain_sample.json`.
  - Covers MY36: 47, MY37: 56, MY38: 45, MY39: 2.
  - Every northern season has 30–41 frames. Elevation runs from −2,585 m to −1,811 m, sols 14–2023.
- **Labelling starts now.** Nothing has been sent to Jev.

## 2026-11-25: Jev probe prepared (not sent)

- **Request format,** from TypeSafe's image and HTTP API docs:
  - The image goes in a top-level `assets` map as base64 JPEG, under a random reference string, and the state holds `{"photo": <ref>}`.
  - Every request needs the header `TypeSafe-Danger-Zone-Images: true`.
  - Images must be 280–1568 px per side. They are rejected, never resized. NASA's 1200×902 browse JPEGs fit.
- **The client,** `marsmon/jev.py`:
  - Builds the four questions from `marsmon/questions.py`, so the wording is the same as on the labelling page.
  - Checks the image size before sending.
  - Raises an error on a failed call instead of treating it as an answer.
  - Converts probabilities into the hand-label vocabulary: above 0.7 is yes, below 0.3 is no, in between is unsure. When there's no ground, the other questions become n/a.
- **What gets logged:** the request with the image replaced by its size and SHA-256, so anyone can re-download the frame from NASA and check it's the same file. Plus the full response and token usage.
- **Probe frames:** `data/probe/terrain_probe_v1.json`, 22 frames that are not in the label sample.
  - 20 random frames, 2 from each tenth of the route (seed 20261126).
  - 2 hard cases picked on purpose: the rover-deck frame (expect no ground) and a sideways view of an open hillside (expect a steep slope).
- **Option-order check (probe only):** each request also asks the terrain question with its five options reversed. TypeSafe notes that a Choice can favour its first option, so a different top answer would show order sensitivity.
- **Dry run:** requests build correctly, every asset is referenced, and the tests pass. Nothing has been downloaded or sent.
