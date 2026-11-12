# Airbnb Vancouver Problem – SFU DSSS DataJam 2026

**Answer:** buy 14 licensed 1-bedroom condos in Downtown, West End and Gastown/Chinatown, 1-night minimum stay. Expected 2027 NOI ≈ $222K (P10 $135K, P90 $319K), 2.3% on all-in cost; a long-term lease on the same units gives 2.4%, so operations decide the edge (Superhost-standard case 3.0%, unverified). Detached houses net about zero.

## Reproduce
1. Put Inside Airbnb Vancouver files in `data/raw/insideairbnb/`: `listings.csv.gz` (detailed), `calendar.csv.gz`, `reviews.csv.gz`.
2. `pip install -r requirements.txt && ./run_all.sh` (outputs land in `outputs/tables`, `data/processed`).
3. The pitch deck is a Claude Slides artifact (Export gives .pptx/PDF); every number on it traces to `outputs/tables/`.

| Script | Produces | Used on slide |
|---|---|---|
| `src/01_clean.py` | cleaning funnel, `comps.csv` | 3, A1–A2 |
| `src/02_worldcup_check.py` | monthly review counts | 8, A2 (decision 5) |
| `src/03_segments.py` | segment and property-type yields | 4, 5 |
| `src/04_validate.py` | validation checks | A4 |
| `src/05_portfolio.py` | Monte Carlo, split-sample test, sensitivity | 8, A4 |
| `src/06_ltr_and_scenarios.py` | short-term vs long-term lease, opt-out scenarios | 6, 9 |
| `src/07_operating_cases.py` | Superhost / 1-night-stay cases, 1BR sensitivity, lease stress | 2, 7, 10 |
| `src/econ.py`, `src/config.py` | all assumptions (prices, costs, haircuts) | A3 |

## Data
Inside Airbnb, Vancouver, CC BY 4.0. **Check the snapshot date:** the files used here carry `last_scraped` 2026-09-17, while the brief names 15 June 2026. REBGV/GVR benchmark prices (May 2026) are hard-coded in `src/config.py` with sources in `docs/assumptions.md`.
