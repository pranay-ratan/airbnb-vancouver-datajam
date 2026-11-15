# Final-round script — Team Pandas

**15 slides, 10 minutes. Divya takes the odd slides, Pranay the even ones.**
The timer in the nav bar turns amber at 9:30 and red at 10:00.
Every figure is read from `outputs/metrics.json`, so this script and the slides cannot disagree.

| # | Slide | Starts | Speaker |
|---|---|---|---|
| 1 | Cover | 0:00 | **DIVYA** |
| 2 | The problem | 0:20 | **PRANAY** |
| 3 | The recommendation | 0:55 | **DIVYA** |
| 4 | The data | 1:35 | **PRANAY** |
| 5 | Few big or many small | 2:50 | **DIVYA** |
| 6 | Where | 3:25 | **PRANAY** |
| 7 | June prices | 4:00 | **DIVYA** |
| 8 | One unit | 4:40 | **PRANAY** |
| 9 | Two calendars | 5:15 | **DIVYA** |
| 10 | The biggest risk | 6:00 | **PRANAY** |
| 11 | Risks and mitigation | 6:40 | **DIVYA** |
| 12 | What didn't hold | 7:15 | **PRANAY** |
| 13 | One home, in 3D | 8:05 | **DIVYA** |
| 14 | Next steps | 8:55 | **PRANAY** |
| 15 | The ask | 9:20 | **DIVYA** |

---

### 1 · Cover — 0:00 — DIVYA

- Good morning — we're Team Pandas: Chitransh, Divya and Pranay
- DDD asked where to put $10M of short-term rental money
- Our answer: 14 small condos downtown, each run on two calendars
- Built only on public data — and the pitch is live: the map, the sliders and the simulation run as we talk

### 2 · The problem — 0:20 — PRANAY

- Three decisions: where, how many and what kind, and how to run them
- You may only rent out the home you live in, and you need a licence
- Leave a home empty six months → Empty Homes Tax plus Speculation and Vacancy Tax: 4% of its value, every year
- What we had to answer it with: one public Inside Airbnb snapshot, plus public prices, rents and tax rules — nothing private, nothing bought

### 3 · The recommendation — 0:55 — DIVYA

- 14 one-bedroom condos: 9 Downtown, 4 in Gastown and Chinatown, 1 in the West End
- $270K of rent left over in 2027, after every cost
- 2.8% a year on the money we spend — price, transfer tax, lawyer, furniture
- We ran 2027 five thousand times; 8 runs in 10 land between $213K and $340K
- All cash, rent only, no bet on prices going up

### 4 · The data — 1:35 — PRANAY

- Our data: Inside Airbnb's Vancouver file, scraped 15 June 2026 — 6,509 listings, 90 columns, a year of calendar ahead, and every review
- We also pulled the December, March and September files — so we could check our answer on data we didn't build it on
- From outside the file: house prices from Greater Vancouver REALTORS, furnished rents from liv.rent, vacancy from CMHC, tax rules from the City and the Province
- How we processed it, left to right on the strip: one public file → clean and filter → fix the June prices → cost out one home → run 2027 five thousand times → check it on September
- The filter, step by step: 6,509 listings → 5,322 whole homes → 3,826 rented by the night → 2,219 a fund could actually buy → 1,981 with both a City licence and a BC registration → 1,037 with a full year of reviews
- Three things we caught before we trusted it: the price is a quote for one stay, not an average; nights booked are estimated from reviews, not recorded — we rebuilt their formula and matched 99.9% of listings; and 27% of whole homes only take stays of 90 nights or more
- Why a full year of reviews: a place listed in March has no year to estimate from. That one rule moved the answer from 1.6% to 2.3%

### 5 · Few big or many small — 2:50 — DIVYA

- Five ways to spend the $10M, each one simulated. Houses lose
- A house keeps 0.4% a year after property tax and repairs — 49% lose money outright
- A condo keeps 2.2%
- That just bought 600 new portfolios for every row — the order never changes
- The reason: costs rise with the price of the home; rent doesn't

### 6 · Where — 3:25 — PRANAY

- A downtown apartment keeps 2.4% a year per dollar spent — from 436 listings we can compare
- Gastown and Chinatown 2.2%; Kitsilano drops to 1.2% — same rent, pricier buildings
- The data files the Gastown towers under Downtown Eastside, but they sell like downtown — so we price them at the west-side price
- Mount Pleasant looks as good, but on only 48 listings — not enough to buy on

### 7 · June prices — 4:00 — DIVYA

- The price in the file is a quote for one stay near the day it was scraped
- Same 2,865 places, checked against September: June costs 16% more
- Up to 37% more in World Cup match weeks — the World Cup is sitting inside the data
- So we cut every June price by 12% before using it
- Taking it as printed would have shown 3.0% instead of 2.3%

### 8 · One unit — 4:40 — PRANAY

- A real listing we can compare to: one bedroom downtown, booked 156 nights a year
- No host, no link, no licence number
- By the night in summer, long stays the rest of the year
- Then the Airbnb fee, the manager, the cleaning, and the cost of owning it
- About $19,000 left over — times 14, that's the $270K

### 9 · Two calendars — 5:15 — DIVYA

- By the night all year: about $220K — about what a normal lease brings in, $228K
- Worse: no six months of long stays → both empty-home taxes → a loss of $152K
- A fifth month by the night breaks the six-month rule — that's the red number
- Half the year's bookings are May to August: by the night then, long stays the rest → $270K

### 10 · The biggest risk — 6:00 — PRANAY

- A city with 3% rental vacancy for two years can ask the Province to drop the live-in-it rule
- Kelowna did, on 1 June 2026
- If Vancouver asks by 28 February, it lands five months into our year — thousands of homes could start renting by the night
- At 20% less by the night: our plan still keeps $232K; by the night alone drops to $153K
- That gap is why the long-stay months exist

### 11 · Risks and mitigation — 6:40 — DIVYA

- Three things could break this — each has a number and a plan
- The rule change: the long-stay months already absorb it
- Overpay by 20% and we keep 2.3% instead of 2.9% → a top price per building, and a year of real bookings from every seller
- The booking numbers here are a guess, not a fact
- Our own reading of the tax rules → a tax lawyer signs off before we buy anything

### 12 · What didn't hold — 7:15 — PRANAY

- We'll tell you what we threw away
- Superhosts look like 168 nights against 132 — but the data turns reviews into nights, and they just have more reviews. Their real calendars look the same. Dropped
- Also tested and lost: one-night minimums, a five-month summer, two-bedrooms, a house with a suite and laneway
- Three limits: one day's scrape; nights are a guess from reviews; prices are area averages, not real buildings
- What held: their booking maths rebuilt and matched for 99.9% of listings; September's data gives 2.2% against 2.3%; the same areas on top in 99% of 300 random half-splits

### 13 · One home, in 3D — 8:05 — DIVYA

- This is one of the 14: a one-bedroom downtown, furnished once for $18,000
- May to August it's listed by the night: self check-in lock, fresh linens and a welcome kit, a cleaner between guests
- About 77 nights booked over the summer
- Then it switches: September to April, listed for stays of 30 nights or more, one tenant at a time — $2,900 a month
- The desk, the full wardrobe, the coat rack — that's what makes a month-long tenant say yes
- Licensed and provincially registered before the first guest
- Same home, same furniture, two calendars — the whole plan in one picture

### 14 · Next steps — 8:55 — PRANAY

- Before buying: written tax advice, and a check of every building — its rules, its licence, a year of real bookings
- By January: furnish, register, find long-stay tenants
- Two numbers to watch: about 77 nights booked per home over the summer, and the 28 February deadline
- Every time new data comes out, we run the whole thing again

### 15 · The ask — 9:20 — DIVYA

- Approve 14 one-bedroom condos downtown, once a tax lawyer signs off
- $270K expected in 2027 on $9.7M, with the risks priced in
- We used Claude to help build the pipeline and this page
- Checked three ways: the data provider's own formulas, a different month's data, and a test that compares every number on screen with what the code produces
- Happy to take questions

---

## What to click (keep this beside the laptop)
- **1 · Cover** — Full screen (F) and reset the timer before you start
- **3 · The recommendation** — Drag the scrubber to the bad end and back
- **4 · The data** — Point along the process strip at the bottom; click the last bar
- **5 · Few big or many small** — Press "Run it again"
- **6 · Where** — Hover Downtown, click it, press "Zoom in"; flick to "Our plan"
- **7 · June prices** — Hover the tallest bar
- **8 · One unit** — Wait for the zoom to land
- **9 · Two calendars** — Click September on, show the red, click it off again
- **10 · The biggest risk** — Drag the slider slowly to 20%
- **12 · What didn't hold** — Click the Superhost card
- **13 · One home, in 3D** — The video plays on its own; click it to pause if a judge asks something

## Q&A — who takes what
Pranay takes the data and the checks (slides 2, 4, 6, 8, 10, 12, 14). Divya takes the money and the plan (slides 3, 5, 7, 9, 11, 13, 15).

- **"Why not houses?"** → 5. Rent goes up with price, but so do property tax, strata fees and repairs
- **"Why only four months by the night?"** → 9, click September on, show the red
- **"What if prices are higher?"** → B, then drag the purchase-price slider
- **"Isn't the booking number just reviews?"** → yes, and we say so: it's why we demand a full year of history and real bookings from every seller
- **"What if Vancouver drops the rule?"** → 10, drag the slider
- **"Slide 9 shows more than $270K."** → slide 9 adds the months up in a straight line so you can watch them change; the headline is the middle of 5,000 simulated years, which also carries the first-year discount and the shocks
- **"How do we know the code is right?"** → 12, and the repo: September's file is different data through the same code
- **"Is the 3D home real?"** → it's our model of one of the 14: a typical downtown one-bedroom layout, furnished to the $18,000 budget in our numbers

## Before you walk in
- Both of you can defend **any of the eight logged decisions** — 9 of the 30 marks, and the judges pick which
- Run it once end to end with the timer going
- Decide whether Chitransh fields questions, so nobody hesitates
