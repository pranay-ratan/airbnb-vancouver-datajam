# The Airbnb Vancouver Problem: SFU DSSS DataJam 2026

**Answer.** Buy 14 one-bedroom condos in Downtown, Gastown/Chinatown and the West End ($9.7M of $10M). Let them by the night May to August and by the month (30+ nights) September to April. Expected 2027 net operating income **$270K** (8 years in 10 between $213K and $340K), a 2.8% return on all-in cost. Return metric: 2027 NOI / (price + BC transfer tax + legal + furnishing), all cash.

Data: Inside Airbnb, Vancouver, 15 June 2026, CC BY 4.0. No host names, listing URLs or licence numbers are published anywhere in this repo.

## Reproduce
1. Download from https://insideairbnb.com/get-the-data/ (Vancouver) into `data/raw/insideairbnb/<date>/` : `listings.csv.gz`, `calendar.csv.gz`, `reviews.csv.gz` for `2026-06-15` (the brief's dataset) and `2026-09-17`; `listings.csv.gz` for `2025-12-14` and `2026-03-21`; `neighbourhoods.geojson` in `data/raw/insideairbnb/`.
2. `pip install -r requirements.txt` then `./run_all.sh` (runs 9 scripts, builds the dashboard, the deck and the interactive pitch, runs the tests).

## Trace any number
| Number on a slide | Script | Output |
|---|---|---|
| Funnel 6,509 → 1,037; data checks | `src/01_profile_clean.py` | `outputs/tables/cleaning_funnel.csv`, `data_profile.json` |
| June vs September price ratio (1.16, 1.14, up to 1.37) | `src/02_price_basis.py` | `price_ratios.csv`, `price_basis.json` |
| Month shares, price index, peak season | `src/03_seasonality.py` | `seasonality.json`, `monthly_stays.csv` |
| Yields by asset, neighbourhood; nightly vs lease vs hybrid per unit | `src/04_unit_economics.py` (costs in `src/assumptions.py`) | `asset_yields.csv`, `segment_yields.csv`, `operating_modes.csv` |
| Portfolio range, strategies, opt-out cases, sensitivities | `src/05_portfolio.py` | `strategies.csv`, `portfolio_modes.csv`, `sensitivity.csv`, `sim_draws.csv` |
| Validation checks | `src/06_validation.py` | `validation.json`, `snapshot_retest.csv`, `listing_age.csv` |
| Decision-log numbers | `src/07_decisions.py` | `decisions.json` |
| "Tested, did not hold" | `src/08_tests_not_held.py` | `tests_not_held.json` |
| Everything quoted in the pitch, deck and dashboard | `src/09_exports.py` | `outputs/metrics.json`, `outputs/dashboard_data.json` |

## Deliverables in this repo
| What | Built by | Output |
|---|---|---|
| **Interactive pitch** (presented live: zoomable map, month toggles, opt-out slider, in-browser Monte Carlo) | `deliverables/build_pitch.py` + `pitch_template.html` | `outputs/pitch/index.html` |
| Slide deck (same analysis, static; exports to .pptx) | `deliverables/build_deck.py` | `deliverables/deck/project/` |
| Dashboard (deep dive) | `deliverables/build_dashboard.py` | `outputs/dashboard/index.html` |
| 3D room tour (one home, summer set-up switching to winter set-up; plays on slide 13) | `deliverables/room_tour/build_room_tour.py` + `scene.html` (three.js) | `outputs/pitch/room_tour.mp4` |
| Talk script and rubric map | `deliverables/build_script.py` | `docs/talk_script.md`, `docs/rubric_check.md` |

The room tour needs `cd deliverables/room_tour && npm install` and ffmpeg, and takes about six minutes to render, so `run_all.sh` does not rebuild it; run `python3 -I deliverables/room_tour/build_room_tour.py` after the numbers change.

Each builder reads only `metrics.json`, so every figure on a slide comes from the table above. The pitch and the dashboard re-run the same unit economics and Monte Carlo in the browser: `build_pitch.py` lifts that JavaScript verbatim out of `dashboard_template.html`, which mirrors `src/04_unit_economics.py` and `src/05_portfolio.py`.

## Method in brief
Comparable listings: entire, licensed (City licence and BC registration both shown), nightly market, apartment/townhouse/3+ bedroom house, first review 12+ months before the scrape. June quotes are divided by the same-listing June/September ratio (the June file quotes World Cup weeks). Costs: Greater Vancouver REALTORS benchmark prices (Aug 2026), strata, property tax, upkeep, 15.5% Airbnb fee, manager and cleaning. Portfolios are filled with real comparable listings until $10M runs out, with demand, price, unit and licence-suspension shocks.

## Limits
One day's scrape; occupancy and revenue are Inside Airbnb estimates; licence status is an estimate; purchase prices are area benchmarks; furnished rent and off-season occupancy are assumptions; the vacancy-tax and tenancy reading needs counsel. See the deck appendix.

## AI use
Claude (Anthropic) wrote the pipeline, simulation, dashboard and slide text under the team's direction. Checks: Inside Airbnb's own revenue and occupancy formulas reproduced (`06_validation.py`), re-run on the September snapshot, and `tests/check_numbers.py` compares published figures with script output.
