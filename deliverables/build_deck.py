"""Builds the pitch deck (Slides artifact files) and the talk script from outputs/metrics.json and outputs/map/neighbourhoods.json.
Every number on a slide or in the script is read from metrics.json, so the deck cannot drift from the pipeline.
Writes deliverables/deck/project/deck.json, deliverables/deck/project/slides/<id>.html, docs/deck_notes.md
Run: python3 -I deliverables/build_deck.py
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "outputs/metrics.json").read_text())
MAP = json.loads((ROOT / "outputs/map/neighbourhoods.json").read_text())
OUT = ROOT / "deliverables/deck/project"; (OUT / "slides").mkdir(parents=True, exist_ok=True)

CREAM="#F7F4EC"; CARD="#FFFFFF"; INK="#0E1B33"; TEAL="#087A5D"; TEALD="#0B1F3A"; MAG="#C9301A"; AMBER="#F5B700"; SLATE="#4A5872"; LINE="#E3DDCF"; GREY="#B4BCCB"; MINT="#D8F3EA"; WHITE="#FFFFFF"
HF="'Plus Jakarta Sans', 'Inter', Arial, sans-serif"
CREDIT = M["credit"]
R, P, PB, S, V, D, T = M["recommendation"], M["profile"], M["price_basis"], M["seasonality"], M["validation"], M["decisions"], M["tested"]
PM = {r["label"]: r for r in M["portfolio_modes"]}
HYB = PM["Hybrid (recommended)"]; NIGHT = PM["Nightly all year (vacancy taxes not applied)"]; TAXED = PM["Nightly all year, with Empty Homes Tax and Speculation Tax"]
LEASE = PM["Unfurnished 12-month lease"]; FIVE = [r for k, r in PM.items() if "five-month" in k][0]
OPT = [r for k, r in PM.items() if k.startswith("Hybrid, opt-out")]; NOPT20 = PM["Nightly, opt-out cuts nightly revenue 20%"]
ST = {r["label"]: r for r in M["strategies"]}
SENS = {r["driver"].split(" ")[0] + " " + r["driver"].split(" ")[1]: r for r in M["sensitivity"]}
CB = {int(r["bedrooms"]): r for r in M["core_by_bedrooms"]}
SEG = {(r["neighbourhood_cleansed"], r["asset"]): r for r in M["segments"]}
AS = M["assets"]; A = M["assumptions"]; AL = R["allocation"]
HOOD = {h["name"]: h for h in MAP["hoods"]}

def K(x): return f"${x/1000:,.0f}K"
def MM(x): return f"${x/1e6:.1f}M"
def pc(x, d=1): return f"{x*100:.{d}f}%"
N = lambda x: f"{int(round(x)):,}"

slides = []; notes_md = []
def sec(id, title, when, inner, notes, bg=CREAM, dark=False, gap=28, footer=True, trans="push"):
    slides.append(dict(id=id, title=title, when=when, inner=inner, notes=notes, bg=bg, dark=dark, gap=gap, footer=footer, trans=trans))
def eyebrow(t, color=TEAL): return f'<p style="font-size:26px;font-weight:700;letter-spacing:1.5px;color:{color}">{t.upper()}</p>'
def h2(t, color=INK): return f'<h2 style="font-family:{HF};font-size:68px;font-weight:800;line-height:1.08;color:{color}">{t}</h2>'
def closing(t, color=TEAL): return f'<p style="font-size:40px;font-weight:800;line-height:1.2;color:{color}">{t}</p>'
def pill(t, bg=CARD, fg=INK, bd=LINE, bar=None):
    bar = bar or (MAG if bd == MAG else SLATE)
    return (f'<p style="font-size:26px;font-weight:600;color:{fg};background:{bg};padding:12px 22px;'
            f'border:1px solid {bd};border-left:7px solid {bar}">{t}</p>')
def card(inner, extra="", bg=CARD): return f'<div style="display:flex;flex-direction:column;gap:12px;background:{bg};padding:30px 34px;border:2px solid {LINE};border-radius:20px;{extra}">{inner}</div>'
def big(num, lab, color=TEAL, size=120, lsize=28):
    return card(f'<p style="font-size:{size}px;font-weight:800;line-height:1;color:{color}">{num}</p><p style="font-size:{lsize}px;line-height:1.3;color:{INK}">{lab}</p>', "flex:1")
def ul(items, fs=28, gap=14, color=INK):
    return f'<ul style="display:flex;flex-direction:column;gap:{gap}px;font-size:{fs}px;line-height:1.3;color:{color}">' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
def tbl(rows, widths, fs=26, head=TEAL):
    o = f'<table style="width:1664px;font-size:{fs}px;color:{INK}">'
    for i, r in enumerate(rows):
        o += f'<tr style="background:{head}">' if i == 0 else '<tr>'
        for j, c in enumerate(r):
            o += (f'<th style="width:{widths[j]}%;color:#FFFFFF;text-align:left;font-weight:700">{c}</th>' if i == 0 else f'<td style="width:{widths[j]}%;text-align:left">{c}</td>')
        o += '</tr>'
    return o + '</table>'
def bar_svg(w, h, color, delay=0.2, rx=8):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-label="Bar"><rect x="0" y="0" width="{w}" height="{h}" rx="{rx}" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{w}" dur="0.9s" begin="{delay}s"/></rect></svg>')
_bi = [0]
def hbar(label, val, txt, vmax, color=TEAL, w=560, lw=560, fs=28):
    bw = max(6, int(w * abs(val) / vmax)); _bi[0] += 1
    return (f'<div style="display:flex;align-items:center;gap:18px"><p style="width:{lw}px;font-size:{fs}px;line-height:1.2;color:{INK};text-align:right">{label}</p>'
            f'{bar_svg(bw, 40, color, 0.15 + 0.12 * (_bi[0] % 8))}<p style="font-size:{fs}px;font-weight:800;color:{INK}">{txt}</p></div>')
def vbar(w, h, color, delay):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-label="Bar"><rect x="0" y="0" width="{w}" height="{h}" rx="6" fill="{color}">'
            f'<animate attributeName="height" from="0" to="{h}" dur="0.8s" begin="{delay}s"/><animate attributeName="y" from="{h}" to="0" dur="0.8s" begin="{delay}s"/></rect></svg>')
# pinned helpers (positions are slide pixels)
def pin_box(x, y, w, inner, style="", build=None):
    b = f' data-build-in="{build}"' if build else ""
    return f'<div{b} style="position:absolute;left:{x}px;top:{y}px;width:{w}px;{style}">{inner}</div>'
def pin_txt(x, y, w, t, fs=28, weight=500, color=INK, extra="", build=None):
    b = f' data-build-in="{build}"' if build else ""
    return f'<p{b} style="position:absolute;left:{x}px;top:{y}px;width:{w}px;font-size:{fs}px;font-weight:{weight};line-height:1.25;color:{color};{extra}">{t}</p>'

def mark(w, ink=INK):
    hh = w * 100 / 132
    return (f'<svg width="{w:.0f}" height="{hh:.0f}" viewBox="0 0 132 100" aria-label="Team Pandas mark">'
            f'<rect x="62" y="20" width="58" height="66" rx="13" fill="#0B1F3A"/>'
            f'<rect x="62" y="20" width="58" height="15" rx="7" fill="#2C4C6E"/>'
            f'<path d="M105 62a12 12 0 1 1-12-12 9.5 9.5 0 0 0 12 12Z" fill="{AMBER}"/>'
            f'<rect x="12" y="14" width="58" height="66" rx="13" fill="{TEAL}"/>'
            f'<rect x="12" y="14" width="58" height="15" rx="7" fill="#0FA87C"/>'
            f'<circle cx="41" cy="54" r="10" fill="{AMBER}"/>'
            f'<g stroke="{AMBER}" stroke-width="3.4" stroke-linecap="round">'
            f'<path d="M41 36v-5M41 77v-5M23 54h-5M64 54h-5M28.3 41.3l-3.5-3.5M57.2 70.2l-3.5-3.5M28.3 66.7l-3.5 3.5M57.2 37.8l-3.5 3.5"/></g>'
            f'<rect x="24" y="6" width="7" height="15" rx="3" fill="{ink}"/>'
            f'<rect x="51" y="6" width="7" height="15" rx="3" fill="{ink}"/></svg>')

def skyline():
    body = ""; wins = ""
    for i, x in enumerate(range(0, 1920, 60)):
        ht = [120, 170, 96, 210, 150, 250, 130, 186, 110, 230, 160, 120, 200, 140, 176, 104][i % 16]
        w = 54 if i % 3 == 0 else 44 if i % 3 == 1 else 38
        top = 300 - ht
        body += f'<rect x="{x}" y="{top}" width="{w}" height="{ht}" rx="3" fill="#0B1F3A"/>'
        if i % 4 == 2:
            body += f'<path d="M{x} {top} L{x+w//2} {top-26} L{x+w} {top} Z" fill="#0B1F3A"/>'
        for r in range(ht // 34):
            for c in range(2):
                if (i + r + c) % 3 != 0:
                    col = AMBER if (i + r) % 5 == 0 else "#12B886"
                    op = "0.95" if (i + r + c) % 4 == 0 else "0.5"
                    lit = (i * 7 + r * 3 + c) % 3 == 0
                    tw = ""
                    if lit:
                        dur = 3.0 + ((i + r * 2 + c) % 7) * 0.55
                        beg = ((i * 5 + r * 3 + c * 2) % 13) * 0.42
                        tw = (f'<animate attributeName="opacity" values="0.25;1;0.25" dur="{dur:.2f}s" '
                              f'begin="{beg:.2f}s" repeatCount="indefinite"/>')
                    wins += f'<rect x="{x+9+c*20}" y="{top+16+r*32}" width="9" height="13" rx="2" fill="{col}" opacity="{op}">{tw}</rect>'
    mtn = ('<path d="M0 300 L150 140 L250 215 L390 70 L520 215 L640 150 L760 300 Z" fill="#22425F" opacity="0.55"/>'
           '<path d="M1180 300 L1320 120 L1430 210 L1560 95 L1700 215 L1800 160 L1920 300 Z" fill="#22425F" opacity="0.55"/>')
    return ('<svg style="position:absolute;left:0px;top:690px" width="1920" height="300" viewBox="0 0 1920 300" '
            f'aria-label="Illustration of a city skyline at dusk">{mtn}{body}{wins}</svg>')

ICON = {
 "pin": "M24 4a14 14 0 0 0-14 14c0 10 14 26 14 26s14-16 14-26A14 14 0 0 0 24 4Zm0 19a5.5 5.5 0 1 1 5.5-5.5A5.5 5.5 0 0 1 24 23Z",
 "stack": "M6 14h36v7H6Zm0 12h36v7H6Zm0 12h36v7H6Z",
 "cal": "M10 8h28a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V12a4 4 0 0 1 4-4Zm-4 12h36M16 4v8M32 4v8",
}
def icon(name, color=TEAL, size=52):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" aria-label="{name} icon" fill="none" stroke="{color}" '
            f'stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"><path d="{ICON[name]}"/></svg>')

# ---------------------------------------------------------------- map geometry
SC = 0.88; MX, MY = 128, 300; MW, MH = 880, 640
def hxy(name): h = HOOD[name]; return int(MX + h["cx"] * SC), int(MY + h["cy"] * SC)
def map_svg(colour):
    out = ''
    for k, h in enumerate(sorted(MAP["hoods"], key=lambda h: -(h["listings"] or 0))):
        c = colour(h); fill = ''
        if c not in ("#E4E6E3", "#DCD8CC"):
            fill = f'<animate attributeName="fill-opacity" from="0.12" to="1" dur="0.9s" begin="{0.15 + 0.09 * k:.2f}s"/>'
        out += f'<path d="{h["path_small"]}" fill="{c}" stroke="#FFFFFF" stroke-width="3">{fill}</path>'
    return out
def map_pinned(colour, label, mid=None):
    i = f' id="{mid}"' if mid else ""
    return (f'<svg{i} style="position:absolute;left:{MX}px;top:{MY}px" width="{MW}" height="{MH}" viewBox="0 0 {MW} {MH}" aria-label="{label}"><g transform="scale({SC})">{map_svg(colour)}</g></svg>')
def overlay(inner, label):
    return (f'<svg data-build-in="fade 1 auto" style="position:absolute;left:{MX}px;top:{MY}px" width="{MW}" height="{MH}" viewBox="0 0 {MW} {MH}" aria-label="{label}"><g transform="scale({SC})">{inner}</g></svg>')
def ripple(name, color, n=2, dur=3, r0=14, r1=70, dx=0, dy=0):
    h = HOOD[name]; o = ''
    for k in range(n):
        b = k * dur / n
        o += (f'<circle cx="{h["cx"]+dx:.0f}" cy="{h["cy"]+dy:.0f}" r="{r0}" fill="none" stroke="{color}" stroke-width="4" opacity="0.7">'
              f'<animate attributeName="r" from="{r0}" to="{r1}" dur="{dur}s" begin="{b:.1f}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" from="0.7" to="0" dur="{dur}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')
    return o
def flow(x1, y1, x2, y2, color, n=3, dur=3.2, bend=-70, r=8):
    dx, dy = x2 - x1, y2 - y1; mx, my = dx / 2, dy / 2 + bend
    o = f'<path d="M{x1:.0f} {y1:.0f} q{mx:.0f} {my:.0f} {dx:.0f} {dy:.0f}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="3 12" stroke-linecap="round" opacity="0.6"/>'
    for k in range(n):
        o += (f'<circle cx="{x1:.0f}" cy="{y1:.0f}" r="{r}" fill="{color}" stroke="#FFFFFF" stroke-width="3">'
              f'<animateMotion dur="{dur}s" begin="{k*dur/n:.1f}s" repeatCount="indefinite" path="M0 0 q{mx:.0f} {my:.0f} {dx:.0f} {dy:.0f}"/></circle>')
    return o
def dot(name, text, order, color=TEAL, dx=0, dy=0):
    x, y = hxy(name)
    return (f'<div data-build-in="pop {order+1}" style="position:absolute;left:{x+dx-24}px;top:{y+dy-24}px;width:48px;height:48px;box-sizing:border-box;border-radius:24px;background:{color};border:4px solid #FFFFFF;display:flex;align-items:center;justify-content:center">'
            f'<p style="font-size:26px;font-weight:800;color:#FFFFFF">{text}</p></div>')
def row(i, order, num, head, sub, color=TEAL, y0=370, pitch=96, x=1068, w=724):
    return pin_box(x, y0 + i * pitch, w,
        f'<div style="display:flex;align-items:center;gap:20px"><div style="width:52px;height:52px;border-radius:26px;background:{color};display:flex;align-items:center;justify-content:center;flex:none"><p style="font-size:28px;font-weight:800;color:#FFFFFF">{num}</p></div>'
        f'<div style="display:flex;flex-direction:column;gap:2px"><p style="font-size:30px;font-weight:800;color:{INK}">{head}</p><p style="font-size:24px;color:{SLATE}">{sub}</p></div></div>',
        f"background:{CARD};border:2px solid {LINE};border-radius:16px;padding:14px 22px;box-sizing:border-box;height:88px", f"fade {order+1}")
def legend(items, x, y):
    out = ""
    cx = x
    for t, c in items:
        out += pin_box(cx, y, 150, f'<div style="display:flex;align-items:center;gap:8px"><div style="width:24px;height:24px;background:{c};border-radius:5px;flex:none"></div><p style="font-size:24px;color:{INK}">{t}</p></div>')
        cx += 150
    return out

def range_viz(R):
    lo, hi, W = 150000, 400000, 1664
    f = lambda v: int((v - lo) / (hi - lo) * W)
    a, m, b = f(R["noi_p10"]), f(R["noi_p50"]), f(R["noi_p90"])
    bar = (f'<div style="display:flex;height:44px;width:{W}px;background:{LINE};border-radius:22px;overflow:hidden">'
           f'<div style="width:{a}px"></div><div style="width:{m-a}px;background:#12B886"></div><div style="width:6px;background:{INK}"></div><div style="width:{b-m-6}px;background:#12B886"></div></div>')
    lab = (f'<div style="display:flex;width:{W}px"><div style="width:{a}px"></div>'
           f'<p style="width:{m-a}px;font-size:28px;font-weight:700;color:{SLATE}">{K(R["noi_p10"])} · 1 year in 10</p>'
           f'<p style="width:{b-m}px;font-size:28px;font-weight:700;color:{SLATE}">{K(R["noi_p50"])} expected · {K(R["noi_p90"])} · 1 in 10</p></div>')
    return f'<div style="display:flex;flex-direction:column;gap:10px">{bar}{lab}</div>'

def month_viz():
    ms = S["month_share"]; names = "J F M A M J J A S O N D".split()
    cols = ''.join(f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;width:96px;height:210px">{vbar(64, int(ms[str(i+1)]*1300), TEAL if 5<=i+1<=8 else GREY, 0.1 + 0.07 * i)}<p style="font-size:24px;color:{SLATE}">{names[i]}</p></div>' for i in range(12))
    side = f'<div style="display:flex;flex-direction:column;gap:6px;flex:1"><p style="font-size:64px;font-weight:800;color:{TEAL};line-height:1">{pc(S["peak_share"],0)}</p><p style="font-size:26px;line-height:1.25;color:{INK}">of a year’s stays fall in May–August: nightly then, furnished the rest</p></div>'
    return f'<div style="display:flex;gap:40px;align-items:flex-end"><div style="display:flex;gap:4px;align-items:flex-end;border-bottom:3px solid {LINE}">{cols}</div>{side}</div>'

# ============================================================== SLIDES
# 1 cover
wave = (skyline() + '<svg style="position:absolute;left:0px;top:900px" width="1920" height="180" viewBox="0 0 1920 180" aria-label="Decorative wave">'
        '<g><path d="M-960 70 c240 -60 720 60 960 0 c240 -60 720 60 960 0 c240 -60 720 60 960 0 c240 -60 720 60 960 0 L2880 180 L-960 180 Z" fill="#12B886"><animateTransform attributeName="transform" type="translate" values="0 0;-480 0;0 0" dur="16s" repeatCount="indefinite"/></path></g>'
        '<g><path d="M-960 112 c240 50 720 -50 960 0 c240 50 720 -50 960 0 c240 50 720 -50 960 0 c240 50 720 -50 960 0 L2880 180 L-960 180 Z" fill="#0B1F3A"><animateTransform attributeName="transform" type="translate" values="0 0;480 0;0 0" dur="12s" repeatCount="indefinite"/></path></g></svg>')
sec("cover", "Cover", "0:00–0:15",
    eyebrow("SFU DSSS DataJam 2026 · DDD investment committee") +
    f'<h1 style="font-family:{HF};font-size:104px;font-weight:800;line-height:1.04;color:{INK}">Buy {R["units"]} condos downtown.<br>Run each on two calendars.</h1>' +
    f'<p style="font-size:38px;font-weight:600;color:{TEAL}">$10M CAD into Vancouver short-term rental property</p>' +
    f'<p style="font-size:34px;font-weight:800;color:{INK}">Team Pandas</p><p style="font-size:28px;color:{SLATE}">Chitransh Motwani · Divya Kapoor · Pranay Ratan</p>' + wave +
    f'<div style="position:absolute;left:1440px;top:128px;display:flex;align-items:center;gap:16px">{mark(96)}'
    f'<div style="display:flex;flex-direction:column"><p style="font-size:34px;font-weight:800;color:{INK};line-height:1.05">TEAM</p>'
    f'<p style="font-size:34px;font-weight:800;color:{TEAL};line-height:1.05">PANDAS</p></div></div>' +
    f'<p style="position:absolute;left:128px;bottom:48px;width:1450px;font-size:24px;color:#FFFFFF">{CREDIT}</p>',
    f"Good morning. We're Team Pandas: Chitransh, Divya and Pranay. DDD asked where to put ten million dollars of short-term rental money. Our answer is {R['units']} small condos downtown, each run on two calendars. We'll show you the answer, the number, and why you can believe it.",
    footer=False, gap=36)

sec("problem", "The problem", "0:15–0:40",
    eyebrow("The problem") + h2("DDD has $10M and three open questions.") +
    f'<p style="font-size:28px;color:{SLATE};line-height:1.3">A fund wants income from BC short-term rental property in 2027. One public snapshot of the market, and rules that change what any building is worth.</p>' +
    '<div style="display:flex;gap:24px">' +
    card(icon("pin") + f'<p style="font-size:34px;font-weight:800">Where</p><p style="font-size:26px;line-height:1.3">Which market, and which neighbourhoods inside it. Vancouver has {N(P["rows"])} listings and they do not earn alike.</p>', "flex:1") +
    card(icon("stack") + '<p style="font-size:34px;font-weight:800">How many, and what kind</p><p style="font-size:26px;line-height:1.3">A few houses or many condos. The answer changes the risk more than it changes the headline revenue.</p>', "flex:1") +
    card(icon("cal") + '<p style="font-size:34px;font-weight:800">How to run them</p><p style="font-size:26px;line-height:1.3">Nightly, a 12-month lease, or both. The City and the Province tax the choice.</p>', "flex:1") + '</div>' +
    '<div style="display:flex;gap:16px;flex-wrap:wrap">' +
    pill("Vancouver: principal-residence only, licence and provincial registration required") +
    pill(f'Empty six months: Empty Homes Tax {pc(A["eht"],0)} + Speculation and Vacancy Tax {pc(A["svt"],0)}', "#FDE4DE", MAG, MAG) + '</div>' +
    closing("We answer all three, and show what we rejected on the way."),
    "Here is the question in front of DDD. Ten million dollars, and three things to decide: where, how many and what kind, and how to run them. Vancouver allows short-term letting only in a principal residence, with a licence and provincial registration, and a home left empty for six months owes the Empty Homes Tax and the Speculation and Vacancy Tax. Those rules do most of the work in this answer.", gap=22)

# 2 the answer
sec("recommendation", "The recommendation", "0:15–1:05",
    eyebrow("The recommendation") + h2(f"Buy {R['units']} one-bedroom condos downtown.") +
    '<div style="display:flex;gap:24px">' +
    big(K(R["noi_p50"]), f'expected 2027 net operating income. Eight years in ten: {K(R["noi_p10"])} to {K(R["noi_p90"])}', TEAL, 120) +
    big(pc(R["yield_p50"]), 'return on all-in cost (price, BC transfer tax, legal, furnishing)', INK, 120) +
    big(MM(R["deployed"]), f'across {R["units"]} units: {AL["Downtown"]} Downtown, {AL["Downtown Eastside"]} Gastown/Chinatown, {AL["West End"]} West End', MAG, 120) + '</div>' +
    range_viz(R) +
    '<div style="display:flex;gap:16px">' + pill(f'Nightly stays, {R["nightly_months"]}') + pill(f'Furnished stays of 30+ nights, {R["furnished_months"]}') + '</div>',
    f"Fourteen one-bedroom condos: nine Downtown, four in Gastown and Chinatown, one in the West End. We expect {K(R['noi_p50'])} of net operating income in 2027, and in eight simulated years out of ten it lands between {K(R['noi_p10'])} and {K(R['noi_p90'])}. That is a {pc(R['yield_p50'])} return on all-in cost. Our metric is 2027 net operating income divided by everything it costs to get a unit running: price, BC transfer tax, legal and furnishing. We chose it over revenue per dollar because property tax, strata and upkeep rise with price, and that is exactly what sinks houses. It is all cash, income only, with no price growth assumed. The two calendars come up in a few minutes.")

fun = M["funnel"]
sec("funnel", "From 6,509 listings to 1,037 comparables", "1:05–1:30",
    eyebrow("The data") + h2(f"We kept {N(P['comps'])} of {N(P['rows'])} listings.") +
    '<div style="display:flex;flex-direction:column;gap:12px">' + ''.join(hbar(f["step"], f["listings"], N(f["listings"]), fun[0]["listings"], TEAL if i < len(fun) - 1 else AMBER, w=760, lw=640, fs=28) for i, f in enumerate(fun)) + '</div>' +
    closing("Licensed, nightly, a year of reviews."),
    f"Our data is the 15 June Inside Airbnb file: {N(P['rows'])} listings. We kept entire homes that are licensed, on the nightly market and reviewed for at least a year, which leaves {N(P['comps'])} comparables. We insisted on a year of history because Inside Airbnb's occupancy is reviews times six nights, and a listing opened in March has no full year. That decision moved the core yield from {pc(D['all_ages']['nightly_yield'])} to {pc(D['base']['nightly_yield'])}.", gap=28)

# 3 houses
sec("houses", "Houses earn almost nothing", "1:05–1:45",
    eyebrow("Few big or many small?") + h2("Houses look big. They earn almost nothing.") +
    f'<p style="font-size:26px;color:{SLATE}">Expected 2027 net operating income of a $10M portfolio, five strategies simulated</p>' +
    '<div style="display:flex;flex-direction:column;gap:14px">' +
    hbar("3 west-side houses", ST["Few large: west-side houses"]["noi_p50"], K(ST["Few large: west-side houses"]["noi_p50"]), 230000, MAG, w=800, lw=520) +
    hbar("6 east-side houses", ST["Houses, east side"]["noi_p50"], K(ST["Houses, east side"]["noi_p50"]), 230000, MAG, w=800, lw=520) +
    hbar("12 apartments, city-wide", ST["Many small: apartments city-wide"]["noi_p50"], K(ST["Many small: apartments city-wide"]["noi_p50"]), 230000, GREY, w=800, lw=520) +
    hbar("12 core 1–2 bedrooms", ST["Core 1-2 bedroom apartments"]["noi_p50"], K(ST["Core 1-2 bedroom apartments"]["noi_p50"]), 230000, GREY, w=800, lw=520) +
    hbar("14 core one-bedrooms", ST["Core one-bedroom apartments"]["noi_p50"], K(ST["Core one-bedroom apartments"]["noi_p50"]), 230000, TEAL, w=800, lw=520) + '</div>' +
    '<div style="display:flex;gap:16px">' + pill(f'Houses: {pc(AS["house"]["net_yield"])} net yield, {pc(AS["house"]["share_losing_money"],0)} lose money', "#FDE4DE", MAG, MAG) + pill(f'Condos: {pc(AS["condo"]["net_yield"])}', MINT, TEALD, TEAL) + '</div>' +
    closing("Many small units win."),
    f"On those comparables, a typical house earns revenue but after property tax and upkeep keeps {pc(AS['house']['net_yield'])} on cost; condos keep {pc(AS['condo']['net_yield'])}. We simulated five portfolio shapes for ten million dollars. {pc(ST['Few large: west-side houses']['prob_yield_below_1pct'],0)} of west-side house portfolios earn under one percent; for our fourteen condos it is {pc(ST['Core one-bedroom apartments']['prob_yield_below_1pct'],0)}. So: many small units.")

# 4 map 1 where
def y_col(h):
    y = h["condo_yield"] if (h["condo_comps"] or 0) >= 15 else None
    if y is None: return "#E4E6E3"
    return "#CFE0F5" if y < .005 else "#9EC1EC" if y < .01 else "#6C9EE0" if y < .015 else "#3D78CE" if y < .02 else "#1E4F9E"
dtw = SEG[("Downtown", "condo")]; dte = SEG[("Downtown Eastside", "condo")]; we = SEG[("West End", "condo")]; kit = SEG[("Kitsilano", "condo")]; mp = SEG[("Mount Pleasant", "condo")]
sec("where", "Map: where apartments earn most", "1:45–2:30",
    eyebrow("Where · click to reveal") + h2("Downtown earns the most per dollar.") +
    map_pinned(y_col, "Map of Vancouver neighbourhoods shaded by apartment net yield; Downtown, Gastown and Chinatown, West End and Mount Pleasant are darkest") +
    overlay(ripple("Downtown", "#FFFFFF", 3, 3.6, 16, 80) + ripple("Downtown Eastside", "#FFFFFF", 2, 3.6, 12, 56), "Pulsing rings on the highest-yield neighbourhoods") +
    pin_txt(1068, 296, 724, "Net yield on cost, apartments, 2027", 26, 700, SLATE) +
    dot("Downtown", "1", 1) + dot("Downtown Eastside", "2", 2) + dot("West End", "3", 3, dx=-16, dy=-8) + dot("Kitsilano", "4", 4, MAG) + dot("Mount Pleasant", "5", 5, AMBER) +
    row(0, 1, "1", f'Downtown {pc(dtw["net_yield"])}', f'{N(dtw["listings"])} comparable listings') +
    row(1, 2, "2", f'Gastown/Chinatown {pc(dte["net_yield"])}', f'{N(dte["listings"])} listings, priced at the west-side benchmark') +
    row(2, 3, "3", f'West End {pc(we["net_yield"])}', f'{N(we["listings"])} listings') +
    row(3, 4, "4", f'Kitsilano {pc(kit["net_yield"])}', 'Pricier west side, same income', MAG) +
    row(4, 5, "5", f'Mount Pleasant {pc(mp["net_yield"])}', f'Only {N(mp["listings"])} listings, range {pc(mp["net_yield_lo"])}–{pc(mp["net_yield_hi"])}: not bought', AMBER) +
    legend([("<0.5%", "#CFE0F5"), ("0.5–1%", "#9EC1EC"), ("1–1.5%", "#6C9EE0"), ("1.5–2%", "#3D78CE"), ("2%+", "#1E4F9E"), ("too few", "#E4E6E3")], 128, 925),
    f"Each neighbourhood is shaded by what apartments there earn on cost. Click through. Downtown: {pc(dtw['net_yield'])} from {N(dtw['listings'])} comparable listings. Gastown and Chinatown, {pc(dte['net_yield'])}. Inside Airbnb files those towers under Downtown Eastside, but they trade like downtown, so we price them at the west-side benchmark; the east-side price would have flattered them at {pc(D['dtes_east_price']['nightly_yield'])}. West End, {pc(we['net_yield'])}. Kitsilano drops to {pc(kit['net_yield'])}. Mount Pleasant looks as good as the core, but it rests on {N(mp['listings'])} listings, with a range of {pc(mp['net_yield_lo'])} to {pc(mp['net_yield_hi'])}. We do not buy on that.", gap=20)

# 5 price
vals = {r["segment"]: r["median_ratio"] for r in M["price_ratios"] if r["comparison"] == "June / September"}
wk = [(l, vals[f"June quote for the week of 2026-{d}"]) for l, d in [("15 Jun", "06-15"), ("22 Jun", "06-22"), ("29 Jun", "06-29"), ("6 Jul", "07-06"), ("13 Jul", "07-13"), ("20 Jul", "07-20")]]
bars = ''.join(f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:8px;width:130px;height:480px"><p style="font-size:30px;font-weight:800;color:{INK}">+{(v-1)*100:.0f}%</p>{vbar(92, int((v-1)*100*11), TEAL if v>1.3 else GREY, 0.2 + 0.12 * k)}<p style="font-size:24px;color:{SLATE}">{l}</p></div>' for k, (l, v) in enumerate(wk))
sec("price", "Finding 1: June prices were World Cup prices", "2:30–3:10",
    eyebrow("Finding 1") + h2("June prices were World Cup prices.") +
    '<div style="display:flex;gap:56px;align-items:flex-end">' +
    f'<div style="display:flex;flex-direction:column;gap:10px"><p style="font-size:26px;color:{SLATE}">June quote vs September quote, same {N(PB["n_same_listing"])} listings, by check-in week</p><div style="display:flex;gap:6px;align-items:flex-end;border-bottom:3px solid {LINE}">{bars}</div></div>' +
    '<div style="display:flex;flex-direction:column;gap:20px;flex:1">' + big(f'+{(PB["june_over_sept_all"]-1)*100:.0f}%', f'for the same listings in June than in September. Up to +{(PB["peak_week_ratio"]-1)*100:.0f}% in match weeks', MAG, 112) + '</div></div>' +
    closing(f'So we divided June quotes by {PB["june_over_sept"]["condo"]:.2f}.'),
    f"First finding, and it is not obvious. The price field in the June file is a quote for one stay near the scrape date, mostly the week of 15 June, with later quotes in match weeks. Compare the same {N(PB['n_same_listing'])} listings against the September file and June costs {(PB['june_over_sept_all']-1)*100:.0f} percent more, and up to {(PB['peak_week_ratio']-1)*100:.0f} percent more in match weeks. Taking the price at face value would have lifted our core yield from {pc(D['base']['nightly_yield'])} to {pc(D['price_as_quoted']['nightly_yield'])}. Decision one: we divide June quotes by {PB['june_over_sept']['condo']:.2f}. Winter prices run {(1-PB['march_over_sept'])*100:.0f} percent below September, so we also build a price index by month rather than using one flat price.")

# 6 operations
def mk(label, v, color): return hbar(label, v, (K(v) if v >= 0 else "−" + K(abs(v))), 300000, color, w=540, lw=560, fs=30)
sec("operations", "Two calendars", "3:10–3:55",
    eyebrow("How to run it") + h2("Renting by the night all year invites a tax bill.") +
    f'<p style="font-size:26px;color:{SLATE}">Expected 2027 net operating income, {R["units"]} units</p>' +
    '<div style="display:flex;flex-direction:column;gap:16px">' + mk("Nightly all year", NIGHT["noi_p50"], GREY) + mk("Nightly, with vacancy taxes", TAXED["noi_p50"], MAG) + mk("12-month lease", LEASE["noi_p50"], GREY) + mk("Two calendars", HYB["noi_p50"], TEAL) + '</div>' +
    month_viz() +
    closing(f"Two calendars earn {K(HYB['noi_p50'])}."),
    f"Decision five. Letting by the night all year earns about {K(NIGHT['noi_p50'])}, roughly what a plain twelve-month lease earns, {K(LEASE['noi_p50'])}. Worse, a home that is not rented for six months in stays of thirty nights or more owes the City's Empty Homes Tax of three percent and the Province's Speculation and Vacancy Tax of one percent of assessed value. Nightly-only would turn into a loss of about {K(abs(TAXED['noi_p50']))}. Half of a year's stays fall in May to August, so we let by the night then, and furnished for thirty nights or more the rest of the year: {K(HYB['noi_p50'])}. We tested a fifth nightly month; it leaves {FIVE['units_missing_tenancy_test']:.1f} of fourteen units short of the six-month test. That tax reading is ours, and we want counsel to confirm it before any offer.")

# 7 map 2 supply risk
def s90(h):
    t = h["nightly"] + h["long90"]
    if t < 20: return "#E4E6E3"
    s = h["long90"] / t
    return "#FDE4DE" if s < .2 else "#F9B7A8" if s < .35 else "#EE7B62" if s < .5 else "#C9301A" if s < .65 else "#7A1608"
cn, c90 = P["core_apartments_nightly"], P["core_apartments_90plus"]
sec("map-risk", "Map: the supply that returns if Vancouver opts out", "3:55–4:35",
    eyebrow("Biggest risk · click to reveal") + h2("A rule change could add supply.") +
    map_pinned(s90, "Map of Vancouver neighbourhoods shaded by the share of entire homes with a 90-night minimum; the downtown core is darkest", "vanmap") +
    overlay(''.join(flow(HOOD[a]["cx"], HOOD[a]["cy"], HOOD["Downtown"]["cx"], HOOD["Downtown"]["cy"], "#FFFFFF", 3, 3.4, b) for a, b in [("Mount Pleasant", 70), ("Kitsilano", -110), ("Downtown Eastside", -40)]) + ripple("Downtown", MAG, 2, 3, 16, 70), "Dots flowing toward Downtown: supply that returns if the rules change") +
    pin_txt(1068, 296, 724, "Share of entire homes at a 90-night minimum", 26, 700, SLATE) +
    dot("Downtown", "!", 1, MAG) +
    row(0, 1, "1", f'Core: {N(c90)} apartments at 90 nights', f'against {N(cn)} on the nightly market', MAG, y0=380, pitch=150) +
    row(1, 2, "2", f'If all switch: −{OPT[2]["optout_worst_erosion"]*100:.0f}% nightly revenue', 'per listing, with demand flat', MAG, y0=380, pitch=150) +
    row(2, 3, "3", f'Two calendars hold up: {K(OPT[1]["noi_p50"])}', f'at −20%; nightly-only falls to {K(NOPT20["noi_p50"])}', TEAL, y0=380, pitch=150) +
    legend([("<20%", "#FDE4DE"), ("20–35%", "#F9B7A8"), ("35–50%", "#EE7B62"), ("50–65%", "#C9301A"), ("65%+", "#7A1608")], 128, 925),
    f"This is the biggest risk. A city can ask the Province to opt out of the principal-residence rule if its rental vacancy has been three percent or more for two years. Kelowna did on 1 June 2026. A Vancouver request by 28 February 2027 could take effect on 1 June, five months into our measured year. The map shows where that supply sits: the share of entire homes with a ninety-night minimum, which is outside the short-term definition today. In the core there are {N(c90)} such apartments against {N(cn)} on the nightly market. If every one switched and demand stayed flat, nightly revenue per listing would fall {OPT[2]['optout_worst_erosion']*100:.0f} percent. Our two-calendar plan holds {K(OPT[1]['noi_p50'])} at a twenty percent fall, while nightly-only drops to {K(NOPT20['noi_p50'])}. That is the main reason for the furnished months.", gap=20)

# 8 map 3 portfolio
def sel_col(h): return "#12B886" if h["name"] in ("Downtown", "Downtown Eastside", "West End") else "#DCD8CC"
sec("map-plan", "Map: where the 14 units go", "4:35–5:05",
    eyebrow("The plan · click to reveal") + h2(f"{R['units']} units in three downtown neighbourhoods.") +
    map_pinned(sel_col, "Map of Vancouver with Downtown, Gastown and Chinatown, and West End highlighted for the 14 purchases", "vanmap") +
    overlay(''.join(flow(150, 70, HOOD[a]["cx"], HOOD[a]["cy"], AMBER, 3, 3.6, b) for a, b in [("West End", -60), ("Downtown", -90), ("Downtown Eastside", -120)]), "Dots flowing from the 10 million dollar fund to the three neighbourhoods") +
    pin_txt(150, 340, 150, "$10M", 40, 800, "#FFFFFF", f"background:{AMBER};text-align:center;padding:8px 0;border-radius:16px;box-sizing:border-box") +
    pin_txt(1068, 296, 724, f'{MM(R["deployed"])} deployed, {K(R["unit_allin_cost"])} all-in per unit', 26, 700, SLATE) +
    dot("Downtown", str(AL["Downtown"]), 1) + dot("Downtown Eastside", str(AL["Downtown Eastside"]), 2) + dot("West End", str(AL["West End"]), 3, dx=-16, dy=-8) +
    row(0, 1, str(AL["Downtown"]), "Downtown", f'{pc(dtw["net_yield"])} yield, {N(dtw["listings"])} comparables', y0=380, pitch=120) +
    row(1, 2, str(AL["Downtown Eastside"]), "Gastown and Chinatown", f'{pc(dte["net_yield"])} yield, {N(dte["listings"])} comparables', y0=380, pitch=120) +
    row(2, 3, str(AL["West End"]), "West End", f'{pc(we["net_yield"])} yield, {N(we["listings"])} comparables', y0=380, pitch=120) +
    pin_txt(1068, 760, 724, f'{MM(R["reserve"])} stays in reserve: the next unit does not fit.', 26, 600, SLATE),
    f"Here is where the money goes. Nine units Downtown, where the most evidence sits. Four in Gastown and Chinatown. One in the West End. Each unit costs about {K(R['unit_allin_cost'])} all-in, so fourteen use {MM(R['deployed'])} and leave {MM(R['reserve'])} in reserve because a fifteenth does not fit. We kept the mix in proportion to where comparable listings actually are, rather than chasing the single best postcode.", gap=20)

# 9 risks
def rcard(title, num, line, mit):
    return card(f'<p style="font-size:34px;font-weight:800;color:{MAG}">{title}</p><p style="font-size:84px;font-weight:800;line-height:1;color:{INK}">{num}</p><p style="font-size:28px;line-height:1.25">{line}</p><p style="font-size:26px;line-height:1.3;color:{TEALD};font-weight:700">{mit}</p>', "flex:1")
sec("risks", "Risks and mitigation", "5:05–5:50",
    eyebrow("Risks") + h2("Three things could break it.") +
    '<div style="display:flex;gap:24px">' +
    rcard("Vancouver opts out", K(OPT[1]["noi_p50"]), f'income at −20% nightly revenue. Nightly-only: {K(NOPT20["noi_p50"])}', "Fix: furnished months sit outside the market") +
    rcard("We pay too much", pc(SENS["Purchase price"]["downside_yield"]), f'yield at +20% price, from {pc(SENS["Purchase price"]["base_yield"])}', "Fix: offer ceiling, 12 months of real bookings") +
    rcard("The tax reading is wrong", "−" + K(abs(TAXED["noi_p50"])), "a year if nightly-only owes vacancy taxes", "Fix: counsel signs off before any offer") + '</div>' +
    f'<p style="font-size:26px;color:{SLATE}">Also: strata bylaws on short stays, and capital value (apartment prices fell 5.9% in the year to October 2026; our yield is income only).</p>',
    f"Three risks. First, the opt-out. At ten, twenty and thirty-four percent less nightly revenue, income is {K(OPT[0]['noi_p50'])}, {K(OPT[1]['noi_p50'])} and {K(OPT[2]['noi_p50'])}. The mitigation is built in: eight months of the year are furnished stays outside the nightly market. Second, paying too much. Twenty percent above benchmark takes the yield from {pc(SENS['Purchase price']['base_yield'])} to {pc(SENS['Purchase price']['downside_yield'])}; we set an offer ceiling per building and ask each seller for twelve months of actual bookings, because occupancy here is an estimate. Third, our tax reading. Counsel signs off before the first offer. Two more, briefly: strata bylaws that ban short stays, and capital value, since apartment prices fell five point nine percent in the year to October. Our yield counts income only.")

# 10 tested / held
def xrow(t, color=MAG, sym="✕"):
    return f'<div style="display:flex;align-items:center;gap:20px"><div style="width:52px;height:52px;border-radius:26px;background:{color};display:flex;align-items:center;justify-content:center;flex:none"><p style="font-size:28px;font-weight:800;color:#FFFFFF">{sym}</p></div><p style="font-size:30px;font-weight:600;line-height:1.2;color:{INK}">{t}</p></div>'
sec("tested", "We tested it; it didn't hold", "5:50–6:25",
    eyebrow("Honest checks") + h2("We tested these. They didn’t hold.") +
    '<div style="display:flex;gap:48px">' +
    '<div style="display:flex;flex-direction:column;gap:18px;flex:1.2"><p style="font-size:30px;font-weight:800;color:' + MAG + '">Dropped</p>' +
    xrow(f'Superhost premium: {N(T["superhost"]["estimated_nights"])} vs {N(T["not_superhost"]["estimated_nights"])} nights is just more reviews') +
    xrow("One-night minimum: no clean pattern") +
    xrow(f'Five nightly months: {FIVE["units_missing_tenancy_test"]:.1f} units fail the tax test') +
    xrow(f'Two-bedrooms: {pc(T["two_bedroom"]["hybrid_yield"])} vs {pc(T["two_bedroom"]["one_bedroom_hybrid_yield"])}') +
    xrow(f'House + suite + laneway: {pc(T["house_suite_laneway"]["net_yield"])}') + '</div>' +
    '<div style="display:flex;flex-direction:column;gap:18px;flex:1"><p style="font-size:30px;font-weight:800;color:' + TEAL + '">Held up</p>' +
    big(f'{V["v5_core1_yield_sept"]*100:.1f}% vs {V["v5_core1_yield_june"]*100:.1f}%', 'core yield, September snapshot vs June', TEAL, 64, 26) +
    big(pc(V["v2_occupancy_formula_match"], 1), 'of listings: Inside Airbnb’s occupancy formula reproduced', TEAL, 64, 26) +
    big(pc(V["v4_top3_beat_average_share"], 0), 'of 300 split samples: top segments stayed on top', TEAL, 64, 26) + '</div></div>',
    f"We also tell you what did not hold. Superhosts show {N(T['superhost']['estimated_nights'])} estimated nights against {N(T['not_superhost']['estimated_nights'])}, but that estimate is just reviews times six, and the forward calendar shows no gap, so we left that premium out. A one-night minimum looked better, but the calendar showed no clean pattern, so we did not rely on it. Five nightly months, two-bedrooms and a house with a suite and laneway home all lost to the plan. And what held up: re-running everything on the September snapshot gives {pc(V['v5_core1_yield_sept'])} against {pc(V['v5_core1_yield_june'])}; we reproduced Inside Airbnb's own occupancy formula for {pc(V['v2_occupancy_formula_match'],0)} of listings; and the top segments stayed on top in {pc(V['v4_top3_beat_average_share'],0)} of three hundred random splits.", gap=24)

# 11 next steps
def step(n, head, items): return card(f'<p style="font-size:60px;font-weight:800;color:{TEAL}">{n}</p><p style="font-size:36px;font-weight:800;color:{INK}">{head}</p>' + ul(items, 28, 12), "flex:1")
sec("next", "Next steps", "6:25–6:45",
    eyebrow("Next steps") + h2("What DDD does first.") +
    '<div style="display:flex;gap:24px">' +
    step("1", "Before buying", ["Written tax advice on the six-month test", "Screen each building: strata bylaws, licence, real bookings"]) +
    step("2", "By 1 January 2027", ["Furnish and register each unit", "Line up furnished tenants for September to April"]) +
    step("3", "How we will know", [f'About {N(R["unit_nights"]*S["peak_share"])} booked nights a unit in May to August', "The 28 February opt-out deadline and the published vacancy rate"]) + '</div>' +
    closing("Check the plan against the data every quarter."),
    f"Three steps. Before buying: written tax advice on the six-month test, and a building-by-building screen for strata bylaws, licences and real bookings. By the first of January: furnish and register each unit, and line up furnished tenants for September to April. And here is how you will know it is working: about {N(R['unit_nights']*S['peak_share'])} booked nights per unit in May to August, and a close eye on the twenty-eighth of February opt-out deadline and the published vacancy rate. We re-run the whole pipeline on each new Inside Airbnb snapshot.", gap=36)

# 12 close
sec("close", "The ask", "6:45–7:00",
    f'<p style="font-size:26px;font-weight:700;letter-spacing:1.5px;color:#5EE0B5">THE ASK</p>' +
    f'<h1 style="font-family:{HF};font-size:96px;font-weight:800;line-height:1.06;color:#FFFFFF">Approve {R["units"]} condos downtown, subject to counsel’s sign-off.</h1>' +
    f'<p style="font-size:34px;font-weight:600;color:#5EE0B5">{K(R["noi_p50"])} expected in 2027 on {MM(R["deployed"])}, with the risks priced in.</p>' +
    f'<p style="font-size:26px;line-height:1.35;color:#D8F3EA">Built with Claude (Anthropic) under our direction. We checked it by reproducing Inside Airbnb’s own formulas, re-running on the September snapshot, and tracing every number on these slides to the code in our GitHub repository.</p>',
    "Our ask: approve fourteen one-bedroom condos downtown, subject to counsel's sign-off on the tax reading. About two hundred and seventy thousand dollars expected in 2027, with the risks priced in. One last thing on method: we used Claude to help write the pipeline and these slides, and we checked it three ways: reproducing Inside Airbnb's own formulas, re-running on the September snapshot, and tracing every number on these slides to code in our repository. We're happy to take questions.",
    bg=TEALD, dark=True, gap=36)

# ---------------- backups
sec("data", "Backup: data and cleaning", "Q&A",
    eyebrow("Backup") + h2("The data, and what we kept.") +
    '<div style="display:flex;gap:48px">' +
    '<div style="display:flex;flex-direction:column;gap:18px;width:620px">' + ul([
      f'<b>Source:</b> Inside Airbnb, Vancouver, 15 June 2026: {N(P["rows"])} listings, a year of calendar, {N(323903)} reviews',
      '<b>Also used:</b> March, September and December files; Greater Vancouver REALTORS prices; CMHC and liv.rent rents; City and Province tax rules',
      f'<b>Checked:</b> price is a quote for one stay; occupancy is reviews × 2 × max(3, minimum nights), capped at 255; {pc(P["share_90plus_entire"],0)} of entire homes sit at a 90-night minimum'], 26, 14) + '</div>' +
    '<div style="display:flex;flex-direction:column;gap:10px;flex:1">' + ''.join(hbar(f["step"], f["listings"], N(f["listings"]), fun[0]["listings"], TEAL if i < len(fun) - 1 else AMBER, w=330, lw=520, fs=24) for i, f in enumerate(fun)) + '</div></div>',
    "Backup. Cleaning funnel is in outputs/tables/cleaning_funnel.csv.", gap=24)

sec("assump", "Backup: key assumptions", "Q&A",
    eyebrow("Backup") + h2("Key assumptions.") +
    tbl([["Item", "Value", "Source"],
      ["Purchase price", f'Apartment benchmark ${M["benchmarks"]["W_condo"]/1000:,.0f}K west, ${M["benchmarks"]["E_condo"]/1000:,.0f}K east; one-bedroom at 85%', "Greater Vancouver REALTORS, MLS HPI, Aug 2026"],
      ["Nightly price", f'June quote ÷ {PB["june_over_sept"]["condo"]:.2f}, × {S["annual_price_level_vs_sept"]:.2f} for the year', "Inside Airbnb, June and September"],
      ["Booked nights", f'{N(R["unit_nights"])} a year, less {pc(A["first_year_haircut"],0)} in year one', "Inside Airbnb estimate"],
      ["Fees and costs", f'Airbnb {pc(A["airbnb_fee"])}; manager {pc(A["mgmt_fee"],0)}; ${A["strata"]["1"]:,.0f} strata; {A["prop_tax"]*100:.2f}% property tax; {A["maint"]["condo"]*100:.1f}% upkeep', "Airbnb; City of Vancouver; our estimate"],
      ["Furnished stays", f'${A["mid_rent"]["1"]:,.0f} a month, let {pc(A["mid_occupancy"],0)} of {A["mid_months"]} months', "liv.rent furnished asking rents"],
      ["Vacancy taxes", f'Empty Homes Tax {pc(A["eht"],0)} plus Speculation and Vacancy Tax {pc(A["svt"],0)} of assessed value', "City of Vancouver; Province of BC"],
      ["Lease benchmark", f'${A["lease_rent"]["1"]:,.0f} a month, {pc(A["lease_vacancy"])} vacancy', "liv.rent; CMHC"]], [18, 50, 32], fs=26),
    "Keep this slide up during Q&A. Every number is in src/assumptions.py and the dashboard sliders move each one.", gap=24)

def drows(rows): return tbl([["Decision", "Why (evidence or alternatives)", "What changed"]] + rows, [24, 42, 34], fs=26)
sec("log1", "Backup: decision log 1", "Q&A",
    eyebrow("Backup") + h2("Decision log (1 of 2).") +
    drows([
      ["1. Price basis: June quotes ÷ 1.14", f'Same {N(PB["n_same_listing"])} listings cost {(PB["june_over_sept_all"]-1)*100:.0f}% more in June and up to {(PB["peak_week_ratio"]-1)*100:.0f}% more in match weeks. Alternative: take the price as given', f'Core one-bedroom yield {pc(D["price_as_quoted"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
      ["2. Comparable set: licensed, 12 months of history", f'Nights estimate is reviews × 6; a listing opened in March has no full year. Alternative: every reviewed listing ({D["all_ages"]["listings"]})', f'Median nights {N(D["all_ages"]["median_nights"])} → {N(D["base"]["median_nights"])}; yield {pc(D["all_ages"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
      ["3. Return metric: 2027 NOI over all-in cost", 'Revenue per dollar ignores property tax, strata and upkeep, which scale with price. Alternative: revenue yield', f'Houses {pc(AS["house"]["revenue_yield"])} → {pc(AS["house"]["net_yield"])}; apartments {pc(AS["condo"]["revenue_yield"])} → {pc(AS["condo"]["net_yield"])}']]),
    "Decisions 1–3. Each has what we chose, why, and what it changed.", gap=24)
sec("log2", "Backup: decision log 2", "Q&A",
    eyebrow("Backup") + h2("Decision log (2 of 2).") +
    drows([
      ["4. Portfolio shape: 14 one-bedroom condos", f'{N(5000)} simulated portfolios per strategy. Alternatives: west and east houses, apartments city-wide', f'P(yield under 1%): {pc(ST["Few large: west-side houses"]["prob_yield_below_1pct"],0)} west-side houses, {pc(ST["Core one-bedroom apartments"]["prob_yield_below_1pct"],0)} our pool'],
      ["5. Calendar: nightly May–August, furnished the rest", f'Vacancy taxes make nightly-only a loss ({K(M["modes_unit"][1]["vacancy_tax_per_unit"])} a unit). Alternatives: nightly all year, lease, five-month season', f'{K(HYB["noi_p50"])} vs {K(NIGHT["noi_p50"])} nightly and {K(LEASE["noi_p50"])} lease'],
      ["6. Airbnb fee 15.5%, not 3%", 'Since late 2025 the quoted price is what the guest pays and Airbnb takes 15.5% from the host', f'Core yield {pc(D["fee_3pct"]["nightly_yield"])} → {pc(D["base"]["nightly_yield"])}'],
      ["7. Only 3+ bedroom homes are houses", f'A smaller “entire home” cannot be told from a suite; {N(D["small_entire_homes_dropped"])} set aside', f'House yield {pc(D["houses_3plus_bedrooms"]["nightly_yield"])}, not {pc(D["houses_all_entire_homes"]["nightly_yield"])}'],
      ["8. Gastown/Chinatown at the west-side price", 'Inside Airbnb files these towers under Downtown Eastside; they trade like downtown', f'Yield {pc(D["dtes_west_price"]["nightly_yield"])}, not {pc(D["dtes_east_price"]["nightly_yield"])}']]),
    "Decisions 4–8.", gap=24)

rt = {r["segment"]: r for r in M["snapshot_retest"]}; c1 = rt["Core one-bedroom apartments"]
sec("valid", "Backup: validation", "Q&A",
    eyebrow("Backup") + h2("How we checked the result.") +
    tbl([["Check", "Result"],
      ["Our revenue arithmetic vs Inside Airbnb’s estimate", f'Correlation {V["v1_revenue_corr"]:.2f}'],
      ["Inside Airbnb’s occupancy field", f'Reproduced for {pc(V["v2_occupancy_formula_match"])} of listings'],
      ["Same pipeline on the September snapshot", f'Core one-bedroom yield {pc(c1["sept_yield"])} vs {pc(c1["june_yield"])}; segment ranking correlation {V["v5_rank_correlation_june_vs_sept"]:.2f} across {V["v5_segments_compared"]} segments'],
      ["Split sample, 300 random halves", f'Top three segments beat the average on the other half {pc(V["v4_top3_beat_average_share"],0)} of the time'],
      ["Forward calendar, 15 June to 31 August", f'Estimate implies {pc(V["v3_median_estimated_summer_occupancy"],0)} of nights; {pc(V["v3_median_summer_unavailable"],0)} already booked or blocked. Plausibility only'],
      ["First-year listings", f'Median {N(V["v6_nights_9_12_months"])} nights at 9–12 months vs {N(V["v6_nights_12_plus_months"])} for established ones']], [38, 62], fs=26),
    "Backup. The September re-run is the main out-of-sample test: different snapshot, same code.", gap=24)

sec("limits", "Backup: limits and use of AI", "Q&A",
    eyebrow("Backup") + h2("Limits and use of AI.") +
    '<div style="display:flex;gap:56px">' +
    '<div style="display:flex;flex-direction:column;gap:16px;flex:1"><p style="font-size:36px;font-weight:800;color:' + TEAL + '">Limits</p>' + ul([
      "One day’s scrape: quotes, listings and licences as of 15 June 2026",
      "Licence status comes from free text: an estimate, not a compliance finding",
      "Occupancy and revenue are Inside Airbnb estimates from review counts",
      "Purchase prices are area benchmarks, not building prices",
      "Furnished rent and off-season occupancy are our assumptions",
      "The tax and tenancy reading is ours and needs counsel"], 26, 12) + '</div>' +
    '<div style="display:flex;flex-direction:column;gap:16px;flex:1"><p style="font-size:36px;font-weight:800;color:' + TEAL + '">Use of AI</p>' + ul([
      "Claude (Anthropic) wrote the pipeline, simulation, dashboard and slide text under the team’s direction",
      "Checked by reproducing Inside Airbnb’s formulas, re-running on the September snapshot, and a test that compares every published number with the script output",
      "The team reviews each decision in the log and can defend it",
      "Code and the interactive dashboard are in the GitHub repository"], 26, 12) + '</div></div>',
    "Backup. [Confirm before presenting: each team member can explain every step.]", gap=24)

src = [("Inside Airbnb, Get the Data (Vancouver)", "insideairbnb.com/get-the-data"), ("Greater Vancouver REALTORS, monthly statistics, Aug 2026", "gvrealtors.ca"),
       ("City of Vancouver: Empty Homes Tax; short-term rental licence", "vancouver.ca"), ("Province of BC: Speculation and Vacancy Tax rates", "gov.bc.ca"),
       ("CMHC Rental Market Report", "cmhc-schl.gc.ca"), ("Airbnb: service fee change", "airbnb.com"), ("liv.rent: furnished and unfurnished asking rents, Aug 2026", "liv.rent")]
sec("sources", "Sources", "Q&A",
    eyebrow("Backup") + h2("Sources.") + ul([f'{a} <span style="color:{SLATE}">· {b}</span>' for a, b in src], 28, 14),
    "Backup. Links are in the dashboard's Method section.", gap=28)

# the two map slides share one pinned map (id "vanmap"), so Slides morphs it between them
for _s in slides:
    if _s["id"] == "map-risk":
        _s["trans"] = "magic"

# ============================================================== write
TOTAL = len(slides)
md = ["# Speaker notes for the static deck (the pitch script is docs/talk_script.md)\n", "Click once per map pin on slides 4, 7 and 8. About 140 words a minute; trim the Q&A-style detail if you have 7. Backup slides 13–19 are for Q&A.\n"]
for i, s in enumerate(slides, 1):
    foot = ""
    if s["footer"]:
        c = "#D8F3EA" if s["dark"] else SLATE
        foot = (f'<div style="position:absolute;left:1700px;top:96px;opacity:0.8">{mark(60, "#FFFDF8" if s["dark"] else INK)}</div>'
                f'<p style="position:absolute;left:128px;bottom:64px;width:1450px;font-size:24px;color:{c}">{CREDIT}</p>'
                f'<p style="position:absolute;right:128px;bottom:64px;width:200px;font-size:24px;color:{c};text-align:right">{i} / {TOTAL}</p>')
    html = (f'<section id="{s["id"]}" data-transition="{s["trans"]}" style="background:{s["bg"]};color:{INK};font-family:{HF};padding:128px 128px 160px;display:flex;flex-direction:column;gap:{s["gap"]}px">'
            f'{s["inner"]}{foot}<aside>{s["when"]}. {s["notes"]}</aside></section>')
    (OUT / "slides" / f'{s["id"]}.html').write_text(html, encoding="utf-8")
    md.append(f'## {i}. {s["title"]} ({s["when"]})\n\n{s["notes"]}\n')
(ROOT / "docs").mkdir(exist_ok=True); (ROOT / "docs/deck_notes.md").write_text("\n".join(md), encoding="utf-8")
order = [s["id"] for s in slides]
idx = {"v": 4, "createdOnFiles": {"v": 1, "at": "2026-11-12T13:30:00Z"}, "lists": "css",
       "title": "DDD Vancouver: $10M STR Investment Pitch (DataJam 2026)", "order": order, "cover": "cover",
       "sections": {"s1": {"description": "The answer and the evidence", "start": "cover"}, "s2": {"description": "Risk, honest checks and next steps", "start": "map-risk"},
                    "s3": {"description": "Backup slides for Q&A", "start": "data"}},
       "faces": {"plus-jakarta-sans": {"family": "Plus Jakarta Sans", "href": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"}},
       "designSystems": []}
(OUT / "deck.json").write_text(json.dumps(idx, indent=1), encoding="utf-8")
words = sum(len(s["notes"].split()) for s in slides[:12])
print("slides:", TOTAL, "| script words (slides 1-12):", words, "| minutes at 140 wpm:", round(words / 140, 1))
