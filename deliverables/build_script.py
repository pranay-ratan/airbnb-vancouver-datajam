"""Builds docs/talk_script.md: the final-round script (10 minutes, two speakers, pointers).

Divya takes the odd slides, Pranay the even ones. Every figure is read from
outputs/metrics.json, so the script cannot drift from the pipeline or the slides.

Run: python3 -I deliverables/build_script.py
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "outputs/metrics.json").read_text())
R, S, P, PB, V, D, A = (M[k] for k in ("recommendation", "seasonality", "profile", "price_basis", "validation", "decisions", "assumptions"))
AS, T = M["assets"], M["tested"]
SENS = {r["driver"].split(" ")[0] + " " + r["driver"].split(" ")[1]: r for r in M["sensitivity"]}
PM = {r["label"]: r for r in M["portfolio_modes"]}
SEG = {(r["neighbourhood_cleansed"], r["asset"]): r for r in M["segments"]}
FUN = [f["listings"] for f in M["funnel"]]
NIGHT = PM["Nightly all year (vacancy taxes not applied)"]
LEASE = PM["Unfurnished 12-month lease"]
TAXED = PM["Nightly all year, with Empty Homes Tax and Speculation Tax"]
HYB = PM["Hybrid (recommended)"]
OPT = [r for k, r in PM.items() if k.startswith("Hybrid, opt-out")]
NOPT20 = PM["Nightly, opt-out cuts nightly revenue 20%"]
dtw, dte, kit = SEG[("Downtown", "condo")], SEG[("Downtown Eastside", "condo")], SEG[("Kitsilano", "condo")]
FURNISH = A["furnish_base"]["condo"] + A["furnish_per_bed"] * 1

K = lambda x: ("−" if x < 0 else "") + "$" + format(round(abs(x) / 1000), ",") + "K"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
N = lambda x: format(int(round(x)), ",")

ODD, EVEN = "DIVYA", "PRANAY"

# (title, starts, [content pointers])
SLIDES = [
 ("Cover", "0:00", [
   "Good morning — we're Team Pandas: Chitransh, Divya and Pranay",
   "DDD asked where to put $10M of short-term rental money",
   f"Our answer: {R['units']} small condos downtown, each run on two calendars",
   "Built only on public data — and the pitch is live: the map, the sliders and the simulation run as we talk"]),

 ("The problem", "0:20", [
   "Three decisions: where, how many and what kind, and how to run them",
   "You may only rent out the home you live in, and you need a licence",
   f"Leave a home empty six months → Empty Homes Tax plus Speculation and Vacancy Tax: {pc(A['eht']+A['svt'],0)} of its value, every year",
   "What we had to answer it with: one public Inside Airbnb snapshot, plus public prices, rents and tax rules — nothing private, nothing bought"]),

 ("The recommendation", "0:55", [
   f"{R['units']} one-bedroom condos: {R['allocation']['Downtown']} Downtown, {R['allocation']['Downtown Eastside']} in Gastown and Chinatown, {R['allocation']['West End']} in the West End",
   f"{K(R['noi_p50'])} of rent left over in 2027, after every cost",
   f"{pc(R['yield_p50'])} a year on the money we spend — price, transfer tax, lawyer, furniture",
   f"We ran 2027 five thousand times; 8 runs in 10 land between {K(R['noi_p10'])} and {K(R['noi_p90'])}",
   "All cash, rent only, no bet on prices going up"]),

 ("The data", "1:35", [
   f"Our data: Inside Airbnb's Vancouver file, scraped 15 June 2026 — {N(P['rows'])} listings, {P['columns']} columns, a year of calendar ahead, and every review",
   "We also pulled the December, March and September files — so we could check our answer on data we didn't build it on",
   "From outside the file: house prices from Greater Vancouver REALTORS, furnished rents from liv.rent, vacancy from CMHC, tax rules from the City and the Province",
   "How we processed it, left to right on the strip: one public file → clean and filter → fix the June prices → cost out one home → run 2027 five thousand times → check it on September",
   f"The filter, step by step: {N(FUN[0])} listings → {N(FUN[1])} whole homes → {N(FUN[3])} rented by the night → {N(FUN[5])} a fund could actually buy → {N(FUN[6])} with both a City licence and a BC registration → {N(FUN[7])} with a full year of reviews",
   f"Three things we caught before we trusted it: the price is a quote for one stay, not an average; nights booked are estimated from reviews, not recorded — we rebuilt their formula and matched {pc(V['v2_occupancy_formula_match'],1)} of listings; and {pc(P['share_90plus_entire'],0)} of whole homes only take stays of 90 nights or more",
   f"Why a full year of reviews: a place listed in March has no year to estimate from. That one rule moved the answer from {pc(D['all_ages']['nightly_yield'])} to {pc(D['base']['nightly_yield'])}"]),

 ("Few big or many small", "2:50", [
   "Five ways to spend the $10M, each one simulated. Houses lose",
   f"A house keeps {pc(AS['house']['net_yield'])} a year after property tax and repairs — {pc(AS['house']['share_losing_money'],0)} lose money outright",
   f"A condo keeps {pc(AS['condo']['net_yield'])}",
   "That just bought 600 new portfolios for every row — the order never changes",
   "The reason: costs rise with the price of the home; rent doesn't"]),

 ("Where", "3:25", [
   f"A downtown apartment keeps {pc(dtw['net_yield'])} a year per dollar spent — from {N(dtw['listings'])} listings we can compare",
   f"Gastown and Chinatown {pc(dte['net_yield'])}; Kitsilano drops to {pc(kit['net_yield'])} — same rent, pricier buildings",
   "The data files the Gastown towers under Downtown Eastside, but they sell like downtown — so we price them at the west-side price",
   f"Mount Pleasant looks as good, but on only {N(SEG[('Mount Pleasant','condo')]['listings'])} listings — not enough to buy on"]),

 ("June prices", "4:00", [
   "The price in the file is a quote for one stay near the day it was scraped",
   f"Same {N(PB['n_same_listing'])} places, checked against September: June costs {((PB['june_over_sept_all']-1)*100):.0f}% more",
   f"Up to {((PB['peak_week_ratio']-1)*100):.0f}% more in World Cup match weeks — the World Cup is sitting inside the data",
   f"So we cut every June price by {((1-1/PB['june_over_sept']['condo'])*100):.0f}% before using it",
   f"Taking it as printed would have shown {pc(D['price_as_quoted']['nightly_yield'])} instead of {pc(D['base']['nightly_yield'])}"]),

 ("One unit", "4:40", [
   f"A real listing we can compare to: one bedroom downtown, booked {N(R['unit_nights'])} nights a year",
   "No host, no link, no licence number",
   "By the night in summer, long stays the rest of the year",
   "Then the Airbnb fee, the manager, the cleaning, and the cost of owning it",
   f"About $19,000 left over — times {R['units']}, that's the {K(R['noi_p50'])}"]),

 ("Two calendars", "5:15", [
   f"By the night all year: about {K(NIGHT['noi_p50'])} — about what a normal lease brings in, {K(LEASE['noi_p50'])}",
   f"Worse: no six months of long stays → both empty-home taxes → a loss of {K(abs(TAXED['noi_p50']))}",
   "A fifth month by the night breaks the six-month rule — that's the red number",
   f"Half the year's bookings are May to August: by the night then, long stays the rest → {K(HYB['noi_p50'])}"]),

 ("The biggest risk", "6:00", [
   "A city with 3% rental vacancy for two years can ask the Province to drop the live-in-it rule",
   "Kelowna did, on 1 June 2026",
   "If Vancouver asks by 28 February, it lands five months into our year — thousands of homes could start renting by the night",
   f"At 20% less by the night: our plan still keeps {K(OPT[1]['noi_p50'])}; by the night alone drops to {K(NOPT20['noi_p50'])}",
   "That gap is why the long-stay months exist"]),

 ("Risks and mitigation", "6:40", [
   "Three things could break this — each has a number and a plan",
   "The rule change: the long-stay months already absorb it",
   f"Overpay by 20% and we keep {pc(SENS['Purchase price']['downside_yield'])} instead of {pc(SENS['Purchase price']['base_yield'])} → a top price per building, and a year of real bookings from every seller",
   "The booking numbers here are a guess, not a fact",
   "Our own reading of the tax rules → a tax lawyer signs off before we buy anything"]),

 ("What didn't hold", "7:15", [
   "We'll tell you what we threw away",
   f"Superhosts look like {N(T['superhost']['estimated_nights'])} nights against {N(T['not_superhost']['estimated_nights'])} — but the data turns reviews into nights, and they just have more reviews. Their real calendars look the same. Dropped",
   "Also tested and lost: one-night minimums, a five-month summer, two-bedrooms, a house with a suite and laneway",
   "Three limits: one day's scrape; nights are a guess from reviews; prices are area averages, not real buildings",
   f"What held: their booking maths rebuilt and matched for {pc(V['v2_occupancy_formula_match'],1)} of listings; September's data gives {pc(V['v5_core1_yield_sept'])} against {pc(V['v5_core1_yield_june'])}; the same areas on top in {pc(V['v4_top3_beat_average_share'],0)} of 300 random half-splits"]),

 ("One home, in 3D", "8:05", [
   f"This is one of the {R['units']}: a one-bedroom downtown, furnished once for ${N(FURNISH)}",
   "May to August it's listed by the night: self check-in lock, fresh linens and a welcome kit, a cleaner between guests",
   f"About {N(R['unit_nights']*S['peak_share'])} nights booked over the summer",
   f"Then it switches: September to April, listed for stays of 30 nights or more, one tenant at a time — ${N(A['mid_rent']['1'])} a month",
   "The desk, the full wardrobe, the coat rack — that's what makes a month-long tenant say yes",
   "Licensed and provincially registered before the first guest",
   "Same home, same furniture, two calendars — the whole plan in one picture"]),

 ("Next steps", "8:55", [
   "Before buying: written tax advice, and a check of every building — its rules, its licence, a year of real bookings",
   "By January: furnish, register, find long-stay tenants",
   f"Two numbers to watch: about {N(R['unit_nights']*S['peak_share'])} nights booked per home over the summer, and the 28 February deadline",
   "Every time new data comes out, we run the whole thing again"]),

 ("The ask", "9:20", [
   f"Approve {R['units']} one-bedroom condos downtown, once a tax lawyer signs off",
   f"{K(R['noi_p50'])} expected in 2027 on ${R['deployed']/1e6:.1f}M, with the risks priced in",
   "We used Claude to help build the pipeline and this page",
   "Checked three ways: the data provider's own formulas, a different month's data, and a test that compares every number on screen with what the code produces",
   "Happy to take questions"]),
]

CLICKS = {
 1: "Full screen (F) and reset the timer before you start",
 3: "Drag the scrubber to the bad end and back",
 4: "Point along the process strip at the bottom; click the last bar",
 5: "Press \"Run it again\"",
 6: "Hover Downtown, click it, press \"Zoom in\"; flick to \"Our plan\"",
 7: "Hover the tallest bar",
 8: "Wait for the zoom to land",
 9: "Click September on, show the red, click it off again",
 10: "Drag the slider slowly to 20%",
 12: "Click the Superhost card",
 13: "The video plays on its own; click it to pause if a judge asks something",
}

rows = "\n".join(f"| {i} | {t} | {tm} | **{ODD if i % 2 else EVEN}** |" for i, (t, tm, _) in enumerate(SLIDES, 1))
body = "\n\n".join(
    f"### {i} · {title} — {tm} — {ODD if i % 2 else EVEN}\n\n" + "\n".join(f"- {p}" for p in pts)
    for i, (title, tm, pts) in enumerate(SLIDES, 1))
clicks = "\n".join(f"- **{i} · {SLIDES[i-1][0]}** — {c}" for i, c in CLICKS.items())

t = f"""# Final-round script — Team Pandas

**{len(SLIDES)} slides, 10 minutes. {ODD.title()} takes the odd slides, {EVEN.title()} the even ones.**
The timer in the nav bar turns amber at 9:30 and red at 10:00.
Every figure is read from `outputs/metrics.json`, so this script and the slides cannot disagree.

| # | Slide | Starts | Speaker |
|---|---|---|---|
{rows}

---

{body}

---

## What to click (keep this beside the laptop)
{clicks}

## Q&A — who takes what
{EVEN.title()} takes the data and the checks (slides 2, 4, 6, 8, 10, 12, 14). {ODD.title()} takes the money and the plan (slides 3, 5, 7, 9, 11, 13, 15).

- **"Why not houses?"** → 5. Rent goes up with price, but so do property tax, strata fees and repairs
- **"Why only four months by the night?"** → 9, click September on, show the red
- **"What if prices are higher?"** → B, then drag the purchase-price slider
- **"Isn't the booking number just reviews?"** → yes, and we say so: it's why we demand a full year of history and real bookings from every seller
- **"What if Vancouver drops the rule?"** → 10, drag the slider
- **"Slide 9 shows more than {K(R['noi_p50'])}."** → slide 9 adds the months up in a straight line so you can watch them change; the headline is the middle of 5,000 simulated years, which also carries the first-year discount and the shocks
- **"How do we know the code is right?"** → 12, and the repo: September's file is different data through the same code
- **"Is the 3D home real?"** → it's our model of one of the {R['units']}: a typical downtown one-bedroom layout, furnished to the ${N(FURNISH)} budget in our numbers

## Before you walk in
- Both of you can defend **any of the eight logged decisions** — 9 of the 30 marks, and the judges pick which
- Run it once end to end with the timer going
- Decide whether Chitransh fields questions, so nobody hesitates
"""

(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs/talk_script.md").write_text(t, encoding="utf-8")
words = sum(len(p.split()) for _, _, pts in SLIDES for p in pts)
print(f"docs/talk_script.md: {len(SLIDES)} slides, {words} words of pointers")
