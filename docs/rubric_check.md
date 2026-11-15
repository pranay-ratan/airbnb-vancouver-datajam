# Rubric check — where each of the 30 points is shown

Judges award a point only for what they **see in the pitch, the appendix, or hear in Q&A**.
"Slide" numbers are the interactive pitch; "backup" = press **B**.

## 1 · Data Understanding — 5
| Looked for | Where | Risk |
|---|---|---|
| The business problem | Slide 2 | — |
| The dataset and its source | Slide 4 + credit line on every slide | — |
| Relevant variables | Slide 4 (funnel), backup: assumptions | — |
| Data-quality checks | Slide 4, slide 7 (the price field), backup: validation | — |
| **Stated limitations** | Slide 13 — **say it out loud**, it is now in the script | Lost if nobody says it |

## 2 · Analysis & Validation — 6
| Looked for | Where |
|---|---|
| The approach and why it fits | Slide 5 (five strategies simulated), slide 3 (metric = NOI / all-in cost) |
| Steps from data to results | Slide 4 → 6 → 8 → 9 |
| Quantitative evidence | Every slide; slide 8 is the unit built up line by line |
| A validation or sanity check | Slide 13: September re-run, formula reproduced, 300 split samples |
| Uncertainty | Slide 3 scrubber (P10–P90), slide 12 histogram |

## 3 · Decision Log & Justification — 9  *(the big one)*
Each decision needs **what / why / what it changed**, and must survive Q&A.
Mentioned live, with the change quantified:
1. **Price basis** — June quotes ÷ 1.14 (slide 7). Changed core yield 3.0% → 2.3%.
2. **Comparable set** — licensed, 12 months of history (slide 4). Changed yield 1.6% → 2.3%.
3. **Calendar** — nightly May–Aug, furnished the rest (slide 9). $270K vs $220K nightly, $228K lease.
Five more are in the backup log (metric choice, Airbnb fee, house definition, Gastown pricing, portfolio shape).
**Each of you should be able to defend any one of the eight.**

## 4 · Insights & Recommendations — 6
| Looked for | Where |
|---|---|
| Two distinct data-backed findings | June price inflation (7); houses earn almost nothing (5) |
| Recommendations tied to them | Slide 3, slide 6 |
| Next steps | Slide 14 |
| Expected 2027 performance | Slide 3: $270K |
| A range with key risks and mitigation | Slide 3 scrubber; slides 10 and 11 |

## 5 · Presentation & Communication — 4
| Looked for | Status |
|---|---|
| A clear narrative | Answer first, then evidence, then risk |
| Accurate visuals | Every number generated from metrics.json by one script |
| **Finishing on time** | Script is ~7:00 with slides 4 and 12 cut. **Rehearse with a timer.** |
| Understanding shown in Q&A | The live sliders answer "what if" questions directly |

## What the brief says loses points — and our position
- *A tour of exploratory analysis* — none; every chart carries a decision.
- *Correlation as causation* — we avoid it; the Superhost finding is explicitly rejected as an artefact.
- *Charts without a decision* — each chart ends in a choice.
- *Precision the data cannot support* — we report whole percentages and $K. If you say "0.1 of 14 units", be ready to explain it is a simulation average.
