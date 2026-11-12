#!/usr/bin/env bash
# Reproduces every number in the deck. Needs data/raw/insideairbnb/{listings,calendar,reviews}.csv.gz  (see README).
set -e; cd "$(dirname "$0")/src"
for f in 01_clean 02_worldcup_check 03_segments 04_validate 05_portfolio 06_ltr_and_scenarios 07_operating_cases; do echo "== $f"; python3 -I $f.py; done
