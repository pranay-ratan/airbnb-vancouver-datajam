#!/usr/bin/env bash
# Reproduces every number in the pitch, the deck and the dashboard.
# Needs Inside Airbnb Vancouver files under data/raw/insideairbnb/<date>/ (see README, "Data").
set -e; cd "$(dirname "$0")"
for f in 01_profile_clean 02_price_basis 03_seasonality 04_unit_economics 05_portfolio 06_validation 07_decisions 08_tests_not_held 09_exports; do
  echo "== $f"; python3 -I src/$f.py > /dev/null; done
python3 -I deliverables/build_dashboard.py
python3 -I deliverables/build_deck.py
python3 -I deliverables/build_pitch.py
python3 -I deliverables/build_script.py
python3 -I tests/check_numbers.py
