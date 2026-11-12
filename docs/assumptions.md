# Assumptions (all editable in src/econ.py, src/config.py)
- Purchase price = REBGV/GVR HPI benchmark (May 2026, via GVR stats packages and market reports): Vancouver West house $3,025,000, townhouse $1,331,700, condo $783,300; Vancouver East house $1,654,900, townhouse $1,067,400, condo ~$650,000 (Oct 2025 benchmark ~$651K / Oct 2026 median $640K). Zone mapping of the 23 neighbourhoods is in `config.ZONE`. Downtown Eastside priced at West (Gastown/Chinatown). Bedroom scaling factors are ours.
- Revenue 2027 = asking price x 0.95 realisation x estimated occupancy x 0.95 (event) x 0.90 (new-listing ramp-up).
- Costs: platform 3%, manager 20%, operating 10%, insurance $2,500, licence $1,000, strata (condo $5,500, townhouse $3,000), property tax 0.30%, maintenance 0.3-0.8% of price. PST/MRDT are guest-paid pass-throughs.
- Capital: BC property transfer tax schedule, 0.5% legal, furnishing $20K/$30K/$40K. All-cash.
- Risk: licence suspension 69/3,248 = 2.1% per unit, loses half a year; market shocks occupancy sd 8%, rate sd 5%, per-unit noise 10%.
- Long-term lease benchmark: $2,400/month unfurnished 1BR (Downtown $2,460, West End $2,320 asking, Aug 2026, liv.rent via Daily Hive); 2BR $2,900 (CMHC 2025 rented-condo average); vacancy 1.5% (CMHC 2025); management 6%; same strata/tax/maintenance, $800 insurance, no furnishing.
- Opt-out scenario: Vancouver purpose-built vacancy 2.1% (2024), 3.7% (2025, CMHC). If the 2026 figure is also >=3%, an exemption request by 28 Feb 2027 could take effect 1 Jun 2027; modelled as 10% / 20% revenue erosion for 7 of 12 months.
