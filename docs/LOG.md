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
