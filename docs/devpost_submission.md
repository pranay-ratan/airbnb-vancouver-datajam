# Devpost draft: Team Pandas (SFU DSSS DataJam 2026)

Status: DRAFT. I could not find a public Devpost page for this DataJam, and the case brief names only two deliverables (a pitch and a GitHub repo). If your organisers gave you a Devpost link, paste the fields below into it.

## Project name
Two Calendars: a $10M plan for Vancouver short-term rentals

## Tagline (one line)
Buy 14 one-bedroom condos downtown and run each on two calendars: nightly in May to August, furnished 30+ night stays the rest of the year.

## Team
Chitransh Motwani, Divya Kapoor, Pranay Ratan (SFU)

## Inspiration / the problem
Data-Driven Developments, a fictional fund, must put $10M CAD into BC short-term rental property. The case: where, how many properties and what mix, defended in 7 minutes, with honest uncertainty.

## What it does
- Recommends 14 one-bedroom condos (9 Downtown, 4 Gastown/Chinatown, 1 West End), 9.7M deployed.
- Expected 2027 net operating income $270K (1 year in 10 below $213K, 1 in 10 above $340K); 2.8% on all-in cost.
- Shows why: houses earn almost nothing after property tax and upkeep; nightly-only rental invites Empty Homes Tax and Speculation and Vacancy Tax; furnished months also cushion a possible Vancouver opt-out of the principal-residence rule.

## How we built it
Python pipeline over the 15 June 2026 Inside Airbnb Vancouver snapshot plus public rent, price and tax sources. 6,509 listings cleaned to 1,037 comparables (licensed, nightly, a year of reviews). Unit economics, a 5,000-draw Monte Carlo per strategy, validation against the September snapshot, and a decision log. Interactive dashboard (map, sliders, in-browser simulation) and a Claude Slides pitch deck. Every number on the slides is generated from metrics.json by one script.

## Challenges
- The June price field is a quote for one stay in World Cup weeks; same listings cost +16% vs September, so we rescaled.
- Inside Airbnb occupancy is reviews x 6, so new listings look worse than they are; we required 12 months of history.
- Neighbourhood labels: Gastown/Chinatown towers sit under "Downtown Eastside" but trade like downtown.
- Tax and tenancy rules are our reading and need counsel.

## Accomplishments
Reproduced Inside Airbnb's occupancy formula for 99.9% of listings; September re-run gives core yield 2.2% vs 2.3%; top segments stayed on top in 99% of 300 split samples; and we list what we tested and dropped (Superhost premium, one-night minimum, five-month season, two-bedrooms, house with suite and laneway).

## What we learned
Per-dollar return, not revenue, is the right lens: costs that scale with price are what sink houses.

## What's next
Tax counsel review, building-level screening (strata bylaws, licences, real bookings), re-run on each new snapshot.

## Use of AI
Claude (Anthropic) helped write the pipeline, dashboard and slide text under our direction; checked via formula reproduction, the September re-run, and a test comparing published numbers with script output.

## Built with
Python, pandas, NumPy, GeoPandas-style map projection, Inside Airbnb, Greater Vancouver REALTORS, CMHC, liv.rent, Claude (Slides and artifacts), GitHub

## Links (fill in)
- GitHub: https://github.com/pranay-ratan/airbnb-vancouver-datajam (currently PRIVATE: make it public or add the judges before submitting)
- Dashboard: (publish/share your artifact link)
- Deck: (share your artifact link, or export .pptx from the artifact)
