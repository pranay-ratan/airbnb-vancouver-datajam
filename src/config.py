from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw/insideairbnb"; OD=ROOT/"data/raw/vancouver_open_data"
PROC=ROOT/"data/processed"; TAB=ROOT/"outputs/tables"; FIG=ROOT/"outputs/figures"
for p in (PROC,TAB,FIG): p.mkdir(parents=True,exist_ok=True)
BUDGET=10_000_000
SEED=2026
# Neighbourhood -> REBGV-style price zone (assumption; see docs/assumptions.md)
ZONE={'Downtown':'W','West End':'W','Fairview':'W','Kitsilano':'W','Shaughnessy':'W','Arbutus Ridge':'W','Dunbar Southlands':'W',
'West Point Grey':'W','Kerrisdale':'W','South Cambie':'W','Oakridge':'W','Marpole':'W',
'Mount Pleasant':'E','Strathcona':'E','Downtown Eastside':'W','Grandview-Woodland':'E','Hastings-Sunrise':'E','Kensington-Cedar Cottage':'E',
'Killarney':'E','Renfrew-Collingwood':'E','Riley Park':'E','Sunset':'E','Victoria-Fraserview':'E'}
# REBGV MLS HPI benchmarks, May 2026 (Vancouver West/East) -- see docs/assumptions.md for sources
BENCH={('W','house'):3_025_000,('E','house'):1_654_900,('W','townhouse'):1_331_700,('E','townhouse'):1_067_400,
       ('W','condo'):783_300,('E','condo'):650_000}
