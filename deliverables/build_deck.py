"""Builds the pitch deck (Slides artifact files) from outputs/metrics.json and outputs/map/neighbourhoods.json.
Every number on a slide is read from metrics.json, so the deck cannot drift from the pipeline.
Writes deliverables/deck/project/deck.json and deliverables/deck/project/slides/<id>.html
Run: python3 -I deliverables/build_deck.py
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "outputs/metrics.json").read_text())
MAP = json.loads((ROOT / "outputs/map/neighbourhoods.json").read_text())
OUT = ROOT / "deliverables/deck/project"; (OUT / "slides").mkdir(parents=True, exist_ok=True)

INK="#0F2233"; PAPER="#F4F1EA"; TEAL="#17707A"; AMBER="#E0A030"; SLATE="#52626F"; CARD="#FBFAF6"; LINE="#D9D4C7"; ORANGE="#C8561F"; MUTE="#B7C7D1"; GREY="#A9B1B6"
HF="'Space Grotesk', 'Inter', sans-serif"; BF="'Inter', Arial, sans-serif"
CREDIT = M["credit"]
R, P, PB, S, V, D, T = M["recommendation"], M["profile"], M["price_basis"], M["seasonality"], M["validation"], M["decisions"], M["tested"]
PM = {r["label"]: r for r in M["portfolio_modes"]}
HYB = PM["Hybrid (recommended)"]; NIGHT = PM["Nightly all year (vacancy taxes not applied)"]; TAXED = PM["Nightly all year, with Empty Homes Tax and Speculation Tax"]
LEASE = PM["Unfurnished 12-month lease"]; FIVE = [r for k, r in PM.items() if "five-month" in k][0]
OPT = [r for k, r in PM.items() if k.startswith("Hybrid, opt-out")]
ST = {r["label"]: r for r in M["strategies"]}
SENS = {r["driver"].split(" ")[0] + " " + r["driver"].split(" ")[1]: r for r in M["sensitivity"]}
CB = {int(r["bedrooms"]): r for r in M["core_by_bedrooms"]}
SEG = {(r["neighbourhood_cleansed"], r["asset"]): r for r in M["segments"]}
AS = M["assets"]; A = M["assumptions"]

def K(x): return f"${x/1000:,.0f}K"
def MM(x): return f"${x/1e6:.1f}M"
def pc(x, d=1): return f"{x*100:.{d}f}%"
N = lambda x: f"{int(round(x)):,}"

slides = []
def foot(n, total, dark=False):
    c = MUTE if dark else SLATE
    return (f'<p style="position:absolute;left:128px;bottom:64px;width:1450px;font-size:24px;color:{c}">{CREDIT}</p>'
            f'<p style="position:absolute;right:128px;bottom:64px;width:200px;font-size:24px;color:{c};text-align:right">{n} / {total}</p>')
def sec(id, inner, notes, bg=PAPER, fg=INK, dark=False, gap=32):
    slides.append((id, bg, fg, inner, notes, dark, gap))
def h2(t, color=INK): return f'<h2 style="font-family:{HF};font-size:60px;font-weight:600;line-height:1.1;color:{color}">{t}</h2>'
def card(inner, bg=CARD, extra=""): return f'<div style="display:flex;flex-direction:column;gap:10px;background:{bg};padding:28px 30px;border:1px solid {LINE};border-radius:16px;{extra}">{inner}</div>'
def stat(num, lab, color=TEAL, flex="flex:1"):
    return card(f'<p style="font-family:{HF};font-size:88px;font-weight:600;line-height:1;color:{color}">{num}</p><p style="font-size:28px;line-height:1.25;color:{INK}">{lab}</p>', extra=flex)
def ul(items, fs=30, gap=14, color=INK):
    return f'<ul style="display:flex;flex-direction:column;gap:{gap}px;font-size:{fs}px;line-height:1.3;color:{color}">' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
def tbl(rows, widths, fs=24, head=TEAL):
    o = f'<table style="width:1664px;font-size:{fs}px;color:{INK}">'
    for i, r in enumerate(rows):
        o += f'<tr style="background:{head}">' if i == 0 else '<tr>'
        for j, c in enumerate(r):
            if i == 0: o += f'<th style="width:{widths[j]}%;color:#F4F1EA;text-align:left;font-weight:600">{c}</th>'
            else: o += f'<td style="width:{widths[j]}%;text-align:left">{c}</td>'
        o += '</tr>'
    return o + '</table>'
def hbar(label, val, txt, vmax, color=TEAL, w=560, lw=520, fs=26):
    bw = max(4, int(w * val / vmax))
    return (f'<div style="display:flex;align-items:center;gap:18px"><p style="width:{lw}px;font-size:{fs}px;line-height:1.2;color:{INK};text-align:right">{label}</p>'
            f'<div style="width:{bw}px;height:36px;background:{color};border-radius:6px"></div><p style="font-size:{fs}px;font-weight:600;color:{INK}">{txt}</p></div>')

# ---------------------------------------------------------------- 1 cover
sec("cover",
 f'<p style="font-size:30px;color:{AMBER};font-weight:600">SFU DSSS DataJam 2026 · Recommendation to DDD’s investment committee</p>'
 f'<h1 style="font-family:{HF};font-size:80px;font-weight:600;line-height:1.08;color:{PAPER}">Buy {R["units"]} one-bedroom condos downtown. Let them by the night in summer and by the month the rest of the year.</h1>'
 f'<p style="font-size:34px;line-height:1.35;color:{MUTE}">$10M CAD · City of Vancouver · expected 2027 net operating income {K(R["noi_p50"])} on {MM(R["deployed"])} invested</p>'
 f'<p style="font-size:28px;color:{MUTE}">[Team names]</p>',
 "0:00–0:25. Open with the answer. Prelim round is 7 minutes: slides 2–10; the appendix and slide 11 are for Q&A.", INK, PAPER, True, 40)

# ---------------------------------------------------------------- 2 recommendation
al = R["allocation"]
sec("recommendation",
 h2("The recommendation: 14 small downtown condos, not a few big houses") +
 '<div style="display:flex;gap:24px">' +
 stat(str(R["units"]), f'one-bedroom condos: {al["Downtown"]} Downtown, {al["Downtown Eastside"]} Gastown/Chinatown, {al["West End"]} West End') +
 stat(K(R["noi_p50"]), f'expected 2027 net operating income; 8 years in 10 between {K(R["noi_p10"])} and {K(R["noi_p90"])}') +
 stat(pc(R["yield_p50"]), f'return on all-in cost ({pc(R["yield_p10"])} to {pc(R["yield_p90"])})', INK) +
 stat("+" + K(HYB["noi_p50"] - NIGHT["noi_p50"]), f'a year over letting by the night all year, and +{K(HYB["noi_p50"]-LEASE["noi_p50"])} over a plain lease', ORANGE) + '</div>' +
 ul([f'<b>Return metric:</b> 2027 net operating income divided by all-in cost (price, BC transfer tax, legal, furnishing). All cash, before any capital gain or loss.',
     f'<b>How it runs:</b> nightly stays {R["nightly_months"]}, furnished stays of 30+ nights {R["furnished_months"]}. A unit let only by the night would owe vacancy taxes.',
     f'<b>Why not houses:</b> they earn {pc(AS["house"]["net_yield"])} on cost, apartments {pc(AS["condo"]["net_yield"])}, and {pc(ST["Few large: west-side houses"]["prob_yield_below_1pct"],0)} of simulated west-side-house portfolios land under 1%.'], fs=30),
 f"0:25–1:30. Say the number, the range and the reason. Range is P10–P90 of {N(5000)} simulated portfolios drawn from real comparable listings. All-in cost per unit about {K(R['unit_allin_cost'])}; {MM(R['reserve'])} stays in reserve because the next unit does not fit.")

# ---------------------------------------------------------------- 3 data
fun = M["funnel"]; fb = ''.join(hbar(f["step"], f["listings"], N(f["listings"]), fun[0]["listings"], TEAL if i < len(fun) - 1 else AMBER, w=330, lw=560, fs=24) for i, f in enumerate(fun))
sec("data",
 h2("The question, the data and what we kept") +
 '<div style="display:flex;gap:48px">' +
 '<div style="display:flex;flex-direction:column;gap:20px;width:640px">' + ul([
   "<b>Question:</b> where should $10M earn the most net income in 2027, and what could break the plan?",
   f"<b>Data:</b> Inside Airbnb, Vancouver, 15 June 2026: {N(P['rows'])} listings, a year of calendar, {N(323903)} reviews.",
   "<b>Also used:</b> the March and September snapshots, Greater Vancouver REALTORS benchmark prices, CMHC and liv.rent rents, City and Province tax rules.",
   "<b>Limits:</b> prices are one day’s quotes; occupancy and revenue are Inside Airbnb estimates; licence status is an estimate."], fs=26, gap=16) + '</div>' +
 f'<div style="display:flex;flex-direction:column;gap:12px;flex:1">{fb}</div></div>',
 f"1:30–2:20. We checked the file before using it: the price field is a quote for one stay near the scrape date, estimated nights equal reviews × 2 × max(3, minimum nights) capped at 255 for {pc(P['occ_formula_match_share'])} of listings, and {pc(P['share_90plus_entire'],0)} of entire homes sit at a 90-night minimum, which is outside the short-term rental definition. Funnel is in outputs/tables/cleaning_funnel.csv.")

# ---------------------------------------------------------------- 4 map
W = 880; H = 640; sc = 0.88
def fill(y):
    if y is None: return "#E4E6E3"
    return "#CFE0F5" if y < .005 else "#9EC1EC" if y < .01 else "#6C9EE0" if y < .015 else "#3D78CE" if y < .02 else "#1E4F9E"
paths = ""; labels = ""
shown = {"Mount Pleasant": (20, 30), "Kitsilano": (0, 0)}
for h in MAP["hoods"]:
    y = h["condo_yield"] if (h["condo_comps"] or 0) >= 15 else None
    paths += f'<path d="{h["path_small"]}" fill="{fill(y)}" stroke="#FBFAF6" stroke-width="3"/>'
    if h["name"] in shown and y is not None:
        dx, dy = shown[h["name"]]
        labels += (f'<p style="position:absolute;left:{int(h["cx"]*sc+dx-80)}px;top:{int(h["cy"]*sc+dy-16)}px;width:160px;text-align:center;font-size:24px;font-weight:600;color:{INK}">{h["name"].replace("Downtown Eastside","Gastown/Chinatown")}<br>{pc(y)}</p>')
leg = [("under 0.5%", "#CFE0F5"), ("0.5–1.0%", "#9EC1EC"), ("1.0–1.5%", "#6C9EE0"), ("1.5–2.0%", "#3D78CE"), ("2.0%+", "#1E4F9E"), ("under 15 listings", "#E4E6E3")]
lg = ''.join(f'<div style="display:flex;align-items:center;gap:10px"><div style="width:26px;height:26px;background:{c};border-radius:4px"></div><p style="font-size:24px;color:{INK}">{t}</p></div>' for t, c in leg)
dt = SEG[("Downtown", "condo")]
core_cb = ''.join(f'<p style="font-size:24px;line-height:1.25;color:{INK}"><b>{n}</b> {pc(SEG[(k,"condo")]["net_yield"])}</p>' for n, k in [('Downtown', 'Downtown'), ('West End', 'West End'), ('Gastown/Chinatown', 'Downtown Eastside')])
labels += f'<div style="position:absolute;left:0px;top:8px;width:250px">{core_cb}</div>'
sec("where",
 h2("Where: the downtown core earns the most per dollar") +
 '<div style="display:flex;gap:40px">' +
 f'<div style="position:relative;width:{W}px;height:{H}px;flex:none"><svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-label="Map of Vancouver neighbourhoods shaded by apartment net yield. Downtown, West End, Gastown and Chinatown and Mount Pleasant are darkest."><g transform="scale({sc})">{paths}</g></svg>{labels}</div>' +
 '<div style="display:flex;flex-direction:column;gap:22px;flex:1">' +
 stat(pc(dt["net_yield"]), f'net yield, Downtown apartments ({N(dt["listings"])} comparable listings)', TEAL, "") +
 ul([f'Apartments earn <b>{pc(AS["condo"]["net_yield"])}</b> on cost across the city; the east and west side houses earn under 1%.',
     f'Mount Pleasant matches the core but rests on {SEG[("Mount Pleasant","condo")]["listings"]:.0f} listings (range {pc(SEG[("Mount Pleasant","condo")]["net_yield_lo"])} to {pc(SEG[("Mount Pleasant","condo")]["net_yield_hi"])}), so it stays out.',
     'Gastown and Chinatown towers are priced at the West-side benchmark, not the cheaper East-side one.'], fs=26, gap=14) +
 f'<div style="display:flex;flex-wrap:wrap;gap:8px 22px">{lg}</div></div></div>',
 f"2:20–3:10. Colour is net yield on all-in cost for apartments with at least 15 comparable listings; grey areas have too few to report. Neighbourhood is Inside Airbnb's cleansed field. Downtown {pc(dt['net_yield'])}, Gastown/Chinatown {pc(SEG[('Downtown Eastside','condo')]['net_yield'])}, West End {pc(SEG[('West End','condo')]['net_yield'])}. Decision 8 in the log: pricing of Gastown/Chinatown.")

# ---------------------------------------------------------------- 5 price basis (finding 1)
wk = [("15 Jun", 1.115), ("22 Jun", 1.235), ("29 Jun", 1.371), ("6 Jul", 1.375), ("13 Jul", 1.372), ("20 Jul", 1.203)]
vals = {r["segment"]: r["median_ratio"] for r in M["price_ratios"] if r["comparison"] == "June / September"}
wk = [(l, vals[f"June quote for the week of 2026-{d}"]) for l, d in [("15 Jun", "06-15"), ("22 Jun", "06-22"), ("29 Jun", "06-29"), ("6 Jul", "07-06"), ("13 Jul", "07-13"), ("20 Jul", "07-20")]]
bars = ''.join(f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:8px;width:120px;height:520px"><p style="font-size:30px;font-weight:600;color:{INK}">+{(v-1)*100:.0f}%</p><div style="width:84px;height:{int((v-1)*100*12)}px;background:{TEAL if v>1.3 else GREY};border-radius:6px 6px 0 0"></div><p style="font-size:24px;color:{SLATE}">{l}</p></div>' for l, v in wk)
sec("price",
 h2("Finding 1: June prices were quoted for World Cup weeks") +
 '<div style="display:flex;gap:56px">' +
 f'<div style="display:flex;flex-direction:column;gap:12px"><p style="font-size:26px;color:{SLATE}">June quote vs September quote, same {N(PB["n_same_listing"])} listings, by check-in week in the June file</p><div style="display:flex;gap:10px;align-items:flex-end;border-bottom:2px solid {LINE}">{bars}</div></div>' +
 '<div style="display:flex;flex-direction:column;gap:22px;flex:1">' +
 ul([f'The June file’s price field is a quote for one stay near the scrape date, mostly the week of 15 June, with later quotes in match weeks.',
     f'The same listings cost <b>{(PB["june_over_sept_all"]-1)*100:.0f}% more</b> in June than in September, and up to <b>{(PB["peak_week_ratio"]-1)*100:.0f}% more</b> in match weeks.',
     f'<b>Decision 1:</b> divide June quotes by {PB["june_over_sept"]["condo"]:.2f}. Core one-bedroom yield falls from {pc(D["price_as_quoted"]["nightly_yield"])} to {pc(D["base"]["nightly_yield"])}.',
     f'Winter prices run {(1-PB["march_over_sept"])*100:.0f}% below September, so a flat annual price would overstate the off-season.'], fs=30, gap=20) + '</div></div>',
 f"3:10–4:00. Non-obvious finding one. Taking the price field at face value would have overstated income by about a third. We also had to build a price index by month (Sept = 100; March {PB['march_over_sept']*100:.0f}; July–August {PB['post_cup_summer_ratio']*100:.0f}) because the December file has no prices at all.")

# ---------------------------------------------------------------- 6 few vs many (finding 2)
rows = [("Few large: west-side houses", "3 houses"), ("Houses, east side", "6 houses"), ("Many small: apartments city-wide", "12 apartments"),
        ("Core 1-2 bedroom apartments", "12 apartments"), ("Core one-bedroom apartments", "14 apartments")]
lo, hi = -100000, 360000; tw = 640
def pos(x): return int((x - lo) / (hi - lo) * tw)
line = ""
for lab, nm in rows:
    r = ST[lab]; a, b, m = pos(r["noi_p10"]), pos(r["noi_p90"]), pos(r["noi_p50"]); good = r["noi_p50"] > 150000
    line += (f'<div style="display:flex;align-items:center;gap:18px"><p style="width:420px;font-size:26px;line-height:1.2;text-align:right">{lab.split(": ")[-1]}<br><span style="color:{SLATE};font-size:24px">{nm}</span></p>'
             f'<div style="position:relative;width:{tw}px;height:36px"><div style="position:absolute;left:{pos(0)}px;top:0;width:2px;height:36px;background:{SLATE}"></div>'
             f'<div style="position:absolute;left:{a}px;top:12px;width:{max(6,b-a)}px;height:12px;background:{TEAL if good else GREY};border-radius:6px"></div>'
             f'<div style="position:absolute;left:{m-9}px;top:9px;width:18px;height:18px;background:{INK};border-radius:9px"></div></div>'
             f'<p style="font-size:26px;font-weight:600;width:130px">{K(r["noi_p50"])}</p></div>')
sec("houses",
 h2("Finding 2: many small units beat a few large ones") +
 f'<p style="font-size:28px;color:{SLATE}">2027 net operating income, nightly operation, vacancy taxes left out so property types compare like for like. Dot is the median; bar is 8 years in 10.</p>' +
 f'<div style="display:flex;flex-direction:column;gap:24px">{line}</div>' +
 ul([f'A typical 3+ bedroom house costs {MM(AS["house"]["median_allin_cost"])} all-in, earns {pc(AS["house"]["revenue_yield"])} in revenue and {pc(AS["house"]["net_yield"])} after property tax and upkeep; {pc(AS["house"]["share_losing_money"],0)} lose money.',
     f'<b>Decision 4:</b> {R["units"]} one-bedrooms. P(yield under 1%): {pc(ST["Few large: west-side houses"]["prob_yield_below_1pct"],0)} for west-side houses, {pc(ST["Core one-bedroom apartments"]["prob_yield_below_1pct"],0)} for the recommended pool.'], fs=30, gap=14),
 f"4:00–4:50. Each bar is {N(5000)} simulated portfolios filled from real comparable listings until the $10M runs out, with a market-wide demand shock, a price shock, unit-level noise and the City's licence-suspension rate. Houses fail because their cost scales with price (property tax, upkeep) while revenue does not. Tested: house + suite + laneway home reaches {pc(T['house_suite_laneway']['net_yield'])}, still under apartments, and rests on a lot-premium assumption.", gap=18)

# ---------------------------------------------------------------- 7 operations
def mk(label, v, color=GREY): return hbar(label, max(abs(v), 0.0001), f'{K(v)}' if v >= 0 else f'−{K(abs(v))}', 300000, color, w=520, lw=560, fs=26)
sec("operations",
 h2("Letting by the night all year earns what a lease earns, and risks a tax bill") +
 '<div style="display:flex;gap:56px">' +
 '<div style="display:flex;flex-direction:column;gap:14px;flex:none">' +
 f'<p style="font-size:26px;color:{SLATE}">Expected 2027 net operating income, {R["units"]} units</p>' +
 mk("Nightly all year", NIGHT["noi_p50"]) + mk("Nightly, with vacancy taxes", TAXED["noi_p50"], ORANGE) + mk("Plain 12-month lease", LEASE["noi_p50"]) + mk("Hybrid (recommended)", HYB["noi_p50"], TEAL) +
 mk("Hybrid, five nightly months", FIVE["noi_p50"], GREY) + '</div>' +
 '<div style="display:flex;flex-direction:column;gap:18px;flex:1">' + ul([
   f'Nightly beats a lease for only {pc(CB[1]["share_nightly_beats_lease"],0)} of comparable one-bedrooms.',
   f'A home not rented for 6 months in stays of 30+ nights owes the City’s Empty Homes Tax (3%) and the Province’s Speculation and Vacancy Tax (1%): about {K(M["modes_unit"][1]["vacancy_tax_per_unit"])} a unit.',
   f'<b>Decision 5:</b> nightly {R["nightly_months"]} (49% of a year’s stays), furnished 30+-night stays the other eight months.',
   f'A fifth nightly month leaves {FIVE["units_missing_tenancy_test"]:.1f} of 14 units short of the six-month test, so we did not take it.'], fs=26, gap=14) + '</div></div>',
 f"4:50–5:40. Hybrid {K(HYB['noi_p50'])} versus {K(NIGHT['noi_p50'])} nightly and {K(LEASE['noi_p50'])} lease. Off-season nightly occupancy is only about {pc(V['v7_off_season_nightly_occupancy'],0)}, so the furnished rent of about ${V['v7_furnished_rent_per_day']:.0f} a day wins. Our reading of the vacancy-tax tenancy test (180 days) needs tax counsel before any purchase.")

# ---------------------------------------------------------------- 8 risks
op = OPT
sec("risks",
 h2("Risks and what we would do about each") +
 tbl([["Risk", "Size", "Mitigation"],
      ["Vancouver opts out of the rule from 1 June 2027", f'Core apartments at a 90-night minimum ({N(P["core_apartments_90plus"])}) would add to the {N(P["core_apartments_nightly"])} nightly ones. Income falls to {K(op[0]["noi_p50"])}, {K(op[1]["noi_p50"])} or {K(op[2]["noi_p50"])} at 10%, 20% and 34% less nightly revenue', 'Eight furnished months already sit outside the nightly market; the plan stays above a lease in the worst case'],
      ["Paying more than the benchmark", f'+20% on price: yield {pc(SENS["Purchase price"]["downside_yield"])} instead of {pc(SENS["Purchase price"]["base_yield"])}', 'Offer ceilings per building; skip any unit above the benchmark'],
      ["Fewer booked nights than estimated", f'20% fewer nights: {pc(SENS["Booked nights"]["downside_yield"])}', 'Occupancy is an Inside Airbnb estimate; ask each seller for 12 months of actual bookings'],
      ["Tax or tenancy reading is wrong", f'Nightly-only would lose {K(abs(TAXED["noi_p50"]))} a year; {HYB["units_missing_tenancy_test"]:.1f} units miss the test in simulation', 'Written advice from tax counsel before the first offer'],
      ["Strata bans stays under 30 nights", 'The unit cannot run the summer plan', 'Read each building’s bylaws before an offer'],
      ["Capital value", f'The yield counts income only; a 5.9% apartment price fall (GVR, October 2026) costs about twice a year’s income', 'Not hedged; DDD’s hold period decides']],
     [24, 40, 36], fs=26),
 "5:40–6:30. Say the biggest two out loud: the opt-out and the price paid. The opt-out trigger is a published statistic (3% rental vacancy two years running); the request deadline is 28 February 2027 and the effective date 1 June. Erosion levels come from the ratio of 90-night to nightly core apartments in this file.", gap=24)

# ---------------------------------------------------------------- 9 tested, did not hold
sh, nsh, m1, m2 = T["superhost"], T["not_superhost"], T["min_one_night"], T["min_two_nights"]
sec("tested",
 h2("We tested these and they did not hold") +
 tbl([["Idea", "What the data showed", "What we did"],
      ["Superhosts earn more", f'Estimated nights {N(sh["estimated_nights"])} vs {N(nsh["estimated_nights"])}, but the estimate is reviews × 6 nights. The forward calendar is {pc(sh["summer_nights_unavailable"],0)} vs {pc(nsh["summer_nights_unavailable"],0)} blocked or booked, with no gap', 'Left the premium out of the plan'],
      ["A one-night minimum earns more", f'{N(m1["estimated_nights"])} vs {N(m2["estimated_nights"])} estimated nights, but the calendar shows no clean pattern (summer {pc(m1["summer_nights_unavailable"],0)} vs {pc(m2["summer_nights_unavailable"],0)})', 'Not relied on'],
      ["A fifth nightly month", f'Income {K(T["five_month_season"]["noi_p50"])} vs {K(T["five_month_season"]["recommended_noi_p50"])}; {T["five_month_season"]["units_missing_units" if False else "units_missing_tenancy_test"]:.1f} of 14 units fail the six-month test', 'Kept four months'],
      ["Two-bedroom condos", f'Hybrid yield {pc(T["two_bedroom"]["hybrid_yield"])} vs {pc(T["two_bedroom"]["one_bedroom_hybrid_yield"])} for one-bedrooms', 'One-bedrooms only'],
      ["House with suite and laneway home", f'{pc(T["house_suite_laneway"]["net_yield"])} vs {pc(T["house_suite_laneway"]["core_one_bedroom_yield"])}, and it needs a lot-premium assumption', 'Houses stay out'],
      ["Mount Pleasant", f'{pc(T["mount_pleasant"]["net_yield"])} on {T["mount_pleasant"]["listings"]} listings, range {pc(T["mount_pleasant"]["lo"])} to {pc(T["mount_pleasant"]["hi"])}', 'Too few listings to buy on']],
     [22, 52, 26], fs=28),
 f"6:30–6:50. Say this out loud, it earns points. The forward-calendar rank correlation with the estimate is only {T['rank_corr_estimate_vs_calendar']:.2f}, which is why we do not lean on the estimate for within-segment differences.", gap=24)

# ---------------------------------------------------------------- 10 next steps
sec("next",
 h2("Next steps and how DDD will know it is working") +
 '<div style="display:flex;gap:28px">' +
 card(f'<p style="font-family:{HF};font-size:40px;font-weight:600;color:{TEAL}">Before buying</p>' + ul(["Written tax and tenancy advice on the six-month test.", "Screen buildings: strata bylaws, active City licence, 12 months of real bookings.", "Set an offer ceiling per building."], fs=32, gap=18), extra="flex:1") +
 card(f'<p style="font-family:{HF};font-size:40px;font-weight:600;color:{TEAL}">Before 1 Jan 2027</p>' + ul(["Furnish and list as Inside Airbnb comparables do: licence plus BC registration.", "Sign the furnished-stay channel for September to April.", "Plan to deploy up to $9.7M; hold the rest as reserve."], fs=32, gap=18), extra="flex:1") +
 card(f'<p style="font-family:{HF};font-size:40px;font-weight:600;color:{TEAL}">Signals in 2027</p>' + ul([f'About {N(R["unit_nights"]*S["peak_share"])} booked nights a unit in May to August (49% of {N(R["unit_nights"])}).', "Watch the opt-out deadline (28 February) and the published vacancy rate.", "Re-run the pipeline on each new Inside Airbnb snapshot."], fs=32, gap=18), extra="flex:1") + '</div>',
 "6:50–7:00. Close on the decision: approve 14 one-bedroom condos subject to counsel’s sign-off on the tax reading.", gap=36)

# ---------------------------------------------------------------- 11 assumptions (Q&A)
sec("assump",
 h2("Key assumptions, for Q&A") +
 tbl([["Item", "Value", "Source"],
      ["Purchase price", f'Apartment benchmark ${M["benchmarks"]["W_condo"]/1000:,.0f}K west, ${M["benchmarks"]["E_condo"]/1000:,.0f}K east; one-bedroom at 85%', M["benchmark_source"]],
      ["Nightly price", f'June quote ÷ {PB["june_over_sept"]["condo"]:.2f}, × {S["annual_price_level_vs_sept"]:.2f} for the year', "Inside Airbnb, June and September"],
      ["Booked nights", f'{N(R["unit_nights"])} a year (12 months to June 2026), less {pc(A["first_year_haircut"],0)} in year one', "Inside Airbnb estimate"],
      ["Airbnb fee; manager", f'{pc(A["airbnb_fee"])} of payout; {pc(A["mgmt_fee"],0)} of payout, cleaning ${A["clean_base"]+A["clean_per_bed"]:.0f} a stay', "Airbnb host fee; market range 15–25%"],
      ["Strata, tax, upkeep", f'${A["strata"]["1"]:,.0f} strata; {A["prop_tax"]*100:.2f}% property tax; {A["maint"]["condo"]*100:.1f}% upkeep', "City of Vancouver tax rates; our estimate"],
      ["Furnished stays", f'${A["mid_rent"]["1"]:,.0f} a month, let {pc(A["mid_occupancy"],0)} of {A["mid_months"]} months', "liv.rent furnished asking rents"],
      ["Vacancy taxes", f'Empty Homes Tax {pc(A["eht"],0)} plus Speculation and Vacancy Tax {pc(A["svt"],0)} of assessed value', "City of Vancouver; Province of BC"],
      ["Lease benchmark", f'${A["lease_rent"]["1"]:,.0f} a month, {pc(A["lease_vacancy"])} vacancy', "liv.rent; CMHC"]],
     [20, 48, 32], fs=28),
 "Keep this slide up during Q&A. Every number is in src/assumptions.py and the dashboard sliders move each one.", gap=24)

# ---------------------------------------------------------------- 12 decision log 1
def drows(rows): return tbl([["Decision", "Why (evidence or alternatives)", "What changed"]] + rows, [24, 42, 34], fs=28)
sec("log1",
 h2("Appendix: decision log (1 of 2)") +
 drows([
  ["1. Price basis: June quotes ÷ 1.14", f'Same {N(PB["n_same_listing"])} listings cost {(PB["june_over_sept_all"]-1)*100:.0f}% more in June and up to {(PB["peak_week_ratio"]-1)*100:.0f}% more in match weeks. Alternative: take the price as given', f'Core one-bedroom yield {pc(D["price_as_quoted"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
  ["2. Comparable set: licensed, with 12 months of history", f'The nights estimate is reviews × 6; a listing opened in March has no full year. Alternatives: every reviewed listing ({D["all_ages"]["listings"]})', f'Median nights {N(D["all_ages"]["median_nights"])} → {N(D["base"]["median_nights"])}; yield {pc(D["all_ages"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
  ["3. Return metric: 2027 NOI over all-in cost", 'Revenue per dollar ignores property tax, strata and upkeep, which scale with price. Alternative: revenue yield', f'Houses {pc(AS["house"]["revenue_yield"])} → {pc(AS["house"]["net_yield"])}; apartments {pc(AS["condo"]["revenue_yield"])} → {pc(AS["condo"]["net_yield"])}']]),
 "Decisions 1–3. Each has what we chose, why, and what it changed.", gap=24)
# ---------------------------------------------------------------- 13 decision log 2
sec("log2",
 h2("Appendix: decision log (2 of 2)") +
 drows([
  ["4. Portfolio shape: 14 one-bedroom condos", f'{N(5000)} simulated portfolios per strategy. Alternatives: west and east houses, apartments city-wide', f'P(yield under 1%): {pc(ST["Few large: west-side houses"]["prob_yield_below_1pct"],0)} for west-side houses, {pc(ST["Core one-bedroom apartments"]["prob_yield_below_1pct"],0)} for the pool'],
  ["5. Operating calendar: nightly May–August, furnished the rest", f'Vacancy taxes make a nightly-only unit a loss ({K(M["modes_unit"][1]["vacancy_tax_per_unit"])} a unit). Alternatives: nightly all year, lease, five-month season', f'{K(HYB["noi_p50"])} vs {K(NIGHT["noi_p50"])} nightly and {K(LEASE["noi_p50"])} lease'],
  ["6. Airbnb fee 15.5%, not 3%", 'Since late 2025 the quoted price is what the guest pays and Airbnb takes 15.5% from the host', f'Core yield {pc(D["fee_3pct"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
  ["7. Only 3+ bedroom homes count as houses", f'A smaller “entire home” cannot be told apart from a suite; {N(D["small_entire_homes_dropped"])} small homes set aside', f'House yield {pc(D["houses_3plus_bedrooms"]["nightly_yield"])}, not {pc(D["houses_all_entire_homes"]["nightly_yield"])}'],
  ["8. Gastown/Chinatown at the west-side price", 'Inside Airbnb files these towers under Downtown Eastside; they trade like downtown', f'Yield {pc(D["dtes_west_price"]["nightly_yield"])}, not {pc(D["dtes_east_price"]["nightly_yield"])}']]),
 "Decisions 4–8.", gap=24)

# ---------------------------------------------------------------- 14 validation
rt = {r["segment"]: r for r in M["snapshot_retest"]}; c1 = rt["Core one-bedroom apartments"]
sec("valid",
 h2("Appendix: how we checked the result") +
 tbl([["Check", "Result"],
      ["Our revenue arithmetic against Inside Airbnb’s estimate", f'Correlation {V["v1_revenue_corr"]:.2f}'],
      ["Inside Airbnb’s occupancy field", f'Reviews × 2 × max(3, minimum nights), capped at 255, reproduced for {pc(V["v2_occupancy_formula_match"])} of listings'],
      ["Same pipeline on the September snapshot", f'Core one-bedroom yield {pc(c1["sept_yield"])} vs {pc(c1["june_yield"])}; segment ranking correlation {V["v5_rank_correlation_june_vs_sept"]:.2f} across {V["v5_segments_compared"]} segments'],
      ["Split sample, 300 random halves", f'Top three segments beat the average on the other half {pc(V["v4_top3_beat_average_share"],0)} of the time'],
      ["Forward calendar, 15 June to 31 August", f'Estimate implies {pc(V["v3_median_estimated_summer_occupancy"],0)} of nights; {pc(V["v3_median_summer_unavailable"],0)} already booked or blocked. A plausibility check only'],
      ["First-year listings", f'Median {N(V["v6_nights_9_12_months"])} nights at 9 to 12 months against {N(V["v6_nights_12_plus_months"])} for established ones; {pc(V["v6_share_under_12_months"],0)} of core apartment listings are under a year old']],
     [38, 62], fs=28),
 "Appendix. The September re-run is the main out-of-sample test: different snapshot, same code.", gap=24)

# ---------------------------------------------------------------- 15 limits + AI
sec("limits",
 h2("Appendix: limits and use of AI") +
 '<div style="display:flex;gap:56px">' +
 '<div style="display:flex;flex-direction:column;gap:16px;flex:1"><h3 style="font-family:' + HF + f';font-size:36px;color:{TEAL}">Limits</h3>' + ul([
   "One day’s scrape. Quotes, listings and licences are as of 15 June 2026.",
   "Licence status comes from free text and is an estimate, not a compliance finding.",
   "Occupancy and revenue are Inside Airbnb estimates from review counts.",
   "Purchase prices are area benchmarks, not building-level prices.",
   "Furnished rent and off-season occupancy are our assumptions.",
   "The tax and tenancy reading is ours and needs counsel."], fs=26, gap=12) + '</div>' +
 '<div style="display:flex;flex-direction:column;gap:16px;flex:1"><h3 style="font-family:' + HF + f';font-size:36px;color:{TEAL}">Use of AI</h3>' + ul([
   "Claude (Anthropic) wrote the pipeline, simulation, dashboard and slide text under the team’s direction.",
   "We checked it by reproducing Inside Airbnb’s own revenue and occupancy figures, re-running everything on the September snapshot, and comparing every figure on the slides with the script output.",
   "The team reviews each decision in the log and can defend it.",
   "Code and the interactive dashboard are in the GitHub repository."], fs=26, gap=12) + '</div></div>',
 "Appendix. [Confirm before presenting: each team member can explain every step.]", gap=24)

TOTAL = len(slides)
for i, (id, bg, fg, inner, notes, dark, gap) in enumerate(slides, 1):
    html = (f'<section id="{id}" data-transition="fade" style="background:{bg};color:{fg};font-family:{BF};padding:128px 128px 160px;display:flex;flex-direction:column;gap:{gap}px">'
            f'{inner}{foot(i, TOTAL, dark)}<aside>{notes}</aside></section>')
    (OUT / "slides" / f"{id}.html").write_text(html, encoding="utf-8")
order = [s[0] for s in slides]
idx = {"v": 4, "createdOnFiles": {"v": 1, "at": "2026-11-12T13:30:00Z"}, "lists": "css",
       "title": "DDD Vancouver: $10M STR Investment Pitch (DataJam 2026)", "order": order, "cover": "cover",
       "sections": {"s1": {"description": "The recommendation and the evidence", "start": "cover"},
                    "s2": {"description": "Operations, risks, what did not hold and next steps", "start": "operations"},
                    "s3": {"description": "Appendix: assumptions, decision log, validation, limits", "start": "assump"}},
       "faces": {"inter": {"family": "Inter", "href": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"},
                 "space-grotesk": {"family": "Space Grotesk", "href": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&display=swap"}},
       "designSystems": []}
(OUT / "deck.json").write_text(json.dumps(idx, indent=1), encoding="utf-8")
print("slides:", TOTAL, order)
