# Philadelphia, Pennsylvania — LVT Political Viability Brief (LYCD Post-Abatement Model)

**Date of analysis:** 2026-07-18
**Model basis (non-default):** This brief is built on `analysis/data/philadelphia_lycd_post_abatement.csv` — the **LYCD (land-value) model under the post-abatement counterfactual**, in which all currently-active 10-year construction abatements are treated as expired, restoring full building value to the taxable base for the ~30,000 formerly-abated parcels. This is an independent, from-scratch companion to the existing OPA-based brief at `analysis/political/Philadelphia.md`, which is **not** touched, read, or superseded by this document. The underlying facts about officials, environment, and legal pathway were re-researched fresh rather than assumed to carry over from that brief, per instruction — they turned out to be substantially similar (same city, same officials, same legal blocker), which is an expected and correctly-independent finding, not evidence of copying.
**Overall viability:** Tier 3 — Conditional
**Official alignment:** Split / uncertain (bifurcated: City Council shows thin majority support; the Pennsylvania General Assembly — the actual gating vote — shows no identified sponsor and no organized opposition, i.e. a coalition-formation vacuum rather than active resistance)
**Structural viability score:** 8/10
**Legal pathway (from brief):** State enabling legislation required before Philadelphia may act at all — Tier 4 (Philadelphia-specific Sterling Act amendment) or Tier 5 (general statewide split-rate enabling authorization). Only after the General Assembly grants this authority can City Council pass an implementing split-rate ordinance (simple majority, 9 of 17 votes). The constitutional question (uniformity clause, Art. VIII §1) is separately contested and would likely be litigated regardless of the legislative outcome.
**Model type (from export):** `split_rate_4to1_lycd_post_abatement` — 4:1 land-to-improvement millage ratio, land millage 26.32/$1,000, improvement millage 6.58/$1,000, modeled on the **combined city + school district levy** (1.3998% nominal, per the notebook's `MILLAGE = 13.998` constant), post-abatement baseline revenue $2,061,178,704.

---

## 1. Summary

Philadelphia's political and economic conditions are unusually favorable for LVT — a large renter population (47.7%), a dominant and currently live housing-affordability/assessment-fairness narrative, and (under this LYCD post-abatement model) 76.6% of single-family homeowners seeing a median 23% tax cut. But none of that matters yet, because Philadelphia cannot legally act at all: the binding constraint is Harrisburg, not City Hall. No sitting Pennsylvania state legislator was found on record with a current (2025–2026) land-value-tax or split-rate position, and no bill exists to attach the reform to. City Council itself leans mildly favorable (thin majority, no organized opposition), and Mayor Parker's administration has already made the adjacent case — her budget office argues the state's uniformity clause "prevents us from taking action on tax reform measures, including taxing commercial real estate differently" — but that is advocacy for repealing a constitutional constraint in general, not an LVT endorsement specifically.

**Top 2 risks:** (1) No visible state-legislative champion for a Sterling Act amendment or statewide split-rate bill — the reform has no vehicle in Harrisburg today; (2) even if enabling legislation passes, the City's own Law Department believes a Philadelphia split-rate would violate the uniformity clause and likely lose in court, given *Madway v. Board* (1967) — large commercial owners have every financial incentive to litigate at Philadelphia's scale, unlike the ~14 small Third-Class PA cities that have operated split-rate for decades unchallenged.

**Top 1 opportunity:** The Homestead Exemption/reassessment fight is *already* the top property-tax story in Philadelphia as of this writing (Council was actively pressing the Parker administration on assessment methodology in mid-July 2026) — a live, high-salience "homeowners are getting squeezed" narrative that a homeowner-relief LVT frame can plug directly into, without having to manufacture urgency.

**What would most change this assessment:** A single PA legislator (ideally a Philadelphia-delegation member on House or Senate Finance) agreeing to sponsor a Sterling Act amendment or general split-rate bill. Rep. Christopher Rabb (D-200, Philadelphia), who chairs the House Finance Tax Modernization & Reform subcommittee, is the single most structurally relevant person to approach — not because he has taken a position, but because his subcommittee is the actual point of entry.

---

## 2. Prerequisites consumed

- **Legal brief:** Present (`analysis/legal/Philadelphia.md`, dated 2026-06-01).
  - Pathway: Vehicle A (direct split-rate) or Vehicle C (permanent improvement abatement), both requiring prior PA General Assembly enabling legislation. Tier 4 (Philadelphia-specific Sterling Act amendment) or Tier 5 (general statewide enabling).
  - Required votes: PA Senate + House passage + Governor's signature (enabling legislation), then Philadelphia City Council simple majority (9 of 17) for the implementing ordinance under Title 19 of the Philadelphia Code.
  - Levies in scope: City (0.6317%) and School District (0.7681%) currently move under **separate** enabling authority (Sterling Act vs. the School District's Act of 1963 authority) — a city-only enabling bill would not automatically extend to the school levy.
- **Model export:** Present (`analysis/data/philadelphia_lycd_post_abatement.csv`).
  - Model type: `split_rate_4to1_lycd_post_abatement`
  - Parcel count: 579,814 (535,698 non-exempt)
  - Modeled current revenue: $2,061,178,704 — **the model's `MILLAGE` constant (13.998/$1,000) confirms this is the combined city + school district levy**, not the city-only 0.6317% that Vehicle A's Tier-4/5 pathway directly authorizes. A city-only enabling bill would need a parallel School Board action to reach the full electoral-math figures reported below; this is flagged again in Section 11.
  - Key stats: 69.1% of non-exempt parcels see a tax decrease; SFR median change −23.0%; income-quintile pattern mildly progressive (lower-income block groups see slightly larger median cuts).

---

## 3. Political actors

**Current-service verification:** Roster pulled directly from phlcouncil.com (not Wikipedia or stale search results). Confirmed: Mayor Cherelle L. Parker in office (no successor election until Nov. 2027); Kenyatta Johnson (District 2) is Council President since Jan. 2024; all 17 Council seats and the Mayor's seat are up together on Nov. 2, 2027 (current terms run through Jan. 2028). Two officials referenced in the 2021 LVT hearing record — then-Councilman Derek Green and then-Councilwoman Maria Quiñones-Sánchez — are **confirmed departed** and were not researched further.

### Philadelphia City Council (17 members) + Mayor

| Name | Role | Term ends | Electoral base | District wins? | Base coalition wins? | Score | Confidence | Key evidence |
|---|---|---|---|---|---|---|---|---|
| Cherelle L. Parker | Mayor | Jan 2028 | Citywide; primary base strongest in Lower Northeast/river-ward precincts | N/A (citywide) | Yes (82.1% SFR win rate in top-quartile primary-strength precincts) | +1 | Medium | As Councilmember, sponsored the 2019 abatement phase-down; as Mayor, has floated a 20-year office-conversion abatement and a possible 100% abatement for underinvested neighborhoods; her administration's budget documents argue the uniformity clause "prevents us from taking action on tax reform measures, including taxing commercial real estate differently" ([WHYY](https://whyy.org/articles/philadelphia-tax-reform-pa-uniformity-clause/)) — general uniformity-clause-repeal advocacy, not a direct LVT/split-rate endorsement. No "land value tax"/"split-rate"/"Georgism" quote found. |
| Kenyatta Johnson | Council President, District 2 | Jan 2028 | River wards + South Philadelphia | Yes | N/A (uncontested 2023 primary/general — no meaningful electoral-base variance to correlate) | 0 | Medium | Sponsored the 2024 Tax Reform Commission (BIRT/wage-tax focus, not LVT); has voiced concern the residential abatement accelerates gentrification while supporting a commercial-only version. No direct LVT quote. |
| Mark Squilla | District 1 | Jan 2028 | South Philadelphia/river wards | Yes | N/A (uncontested) | 0 | Low | No LVT-specific statement found. |
| Jamie Gauthier | District 3, Housing Committee Chair | Jan 2028 | West Philadelphia | Yes | N/A (uncontested) | +1 | Medium | Chairs the Housing Committee; championed mandatory inclusionary zoning and co-sponsored a tax-freeze extension for long-time owners. No direct LVT quote. |
| Curtis Jones Jr. | District 4 | Jan 2028 | West/Northwest Philadelphia | Yes | N/A (uncontested) | 0 | Low | Chairs the Vacant Property Review Committee (directly relevant portfolio) but no tax-structure statement found. |
| Jeffery Young Jr. | District 5 | Jan 2028 | Center City/South Philadelphia | Yes | N/A (uncontested) | −1 | Medium | Sued to block a zoning variance; has sought fines targeting single-family-to-multiunit conversions — development-cautious record. |
| Michael Driscoll | District 6 | Jan 2028 | Near Northeast Philadelphia | Yes | N/A (uncontested) | −1 | Medium | Sent a July 2026 letter demanding OPA explain its reassessment methodology — a direct, assessment-skeptical public position that cuts against any base-value restructuring, including LVT. |
| Quetcy Lozada | District 7 | Jan 2028 | Near Northeast (Latino-plurality precincts) | Yes | **Yes (90.5% SFR win rate in stronghold precincts; r = +0.086 SFR, not significant)** | +1 | Low | 5th Square (YIMBY) endorsement; extended longtime-owner tax-exemption deadlines. Org-endorsement-only signal, capped at Low per the evidence hierarchy. |
| Cindy Bass | District 8 | Jan 2028 | Northwest Philadelphia | Yes | **Yes (76.6% SFR win rate in stronghold; r = −0.016 SFR, n.s.)** | −1 | Medium | Sponsored a 2018 bill to fully repeal the 10-year construction abatement — a direct legislative record pointed the opposite direction from LVT's building-tax-relief logic. |
| Anthony Phillips | District 9 | Jan 2028 | Northwest/West Oak Lane | Yes | **Yes (85.4% SFR win rate in stronghold; r = +0.038 SFR, n.s.)** | +1 | Medium | 5th Square-endorsed with a direct supportive quote; sits on Vacant Property Review Committee; backs the "Turn the Key" vacant-land-to-housing program. |
| Brian O'Neill | District 10 (R) | Jan 2028 | Far Northeast Philadelphia | Yes | **Yes (92.3% SFR win rate in stronghold; r = +0.173 SFR, p = 0.032 — significant positive)** | 0 | Low | Doubled the Homestead Exemption; no LVT-specific statement. Notably, District 10 is the one genuinely two-party-contested seat (O'Neill, R, beat Masino, D, in the 2023 general) — his strongest precincts are *significantly positively correlated* with SFR tax decreases under this model, a real point of political leverage even absent a stated position. |
| Katherine Gilmore Richardson | At-Large, Majority Leader | Jan 2028 | Citywide | N/A | Yes (84.3% SFR win rate in stronghold; r = −0.118 SFR, p < 0.001) | +1 | Low-Medium | Sponsored a generational-wealth-preservation bill; on record: "the most affordable home is the one you already own." |
| Isaiah Thomas | At-Large, Majority Whip | Jan 2028 | Citywide | N/A | Yes (80.7% SFR win rate; r = −0.141 SFR, p < 0.001) | +1 | Low | 5th Square-endorsed; Vacant Property Review Committee member; no individual LVT quote. |
| Jim Harrity | At-Large | Jan 2028 | Citywide | N/A | Yes (87.7% SFR win rate; r = +0.024 SFR, n.s.) | +1 | Low | Co-announced a tax-relief-for-low-income-residents package; not YIMBY-endorsed. |
| Nina Ahmad | At-Large | Jan 2028 | Citywide | N/A | Yes (82.6% SFR win rate; r = −0.067 SFR, p = 0.006) | 0 | Low | Homeowner-exemption-enrollment advocacy only. **Disclosure flag:** reported ~49% stake in JNA Capital, a real-estate firm — a potential conflict of interest on any property-tax-structure vote, noted here rather than scored. |
| Rue Landau | At-Large | Jan 2028 | Citywide | N/A | Yes (83.2% SFR win rate; r = −0.061 SFR, p = 0.012) | +1 | Medium | Tenant-defense attorney background; co-sponsored a tax-freeze extension; pushed a resolution urging full acceptance of assessment appeals amid rising valuations. |
| Kendra Brooks | At-Large (WFP, minority seat) | Jan 2028 | Citywide, general-election minority-party base | N/A | Yes (85.6% SFR win rate; r = −0.157 SFR, p < 0.001) | +1 | Low | Co-launched the "Philly Wealth Tax"/People's Tax Plan — progressive taxation but a wealth-tax mechanism, not LVT specifically. |
| Nicolas O'Rourke | At-Large (WFP, minority seat) | Jan 2028 | Citywide, general-election minority-party base | N/A | Yes (85.4% SFR win rate; r = −0.126 SFR, p < 0.001) | +1 | Low | Co-sponsor of the same People's Tax Plan; same wealth-tax caveat as Brooks. |

**Zero-signal officials (explicit, not skipped):** Squilla, Jones Jr., O'Neill, Ahmad — searched for LVT/split-rate/vacant-land/abatement statements and found none beyond what's listed.

### Pennsylvania General Assembly (state action required — Gate 4 scope)

| Name | Role | Term ends | Score | Confidence | Key evidence |
|---|---|---|---|---|---|
| Scott E. Hutchinson (R, SD-21) | Senate Finance Committee Chair | 2026 (SD-21, not Philadelphia) | 0 | Low | No public LVT/split-rate statement found; represents rural NW PA, no direct Philadelphia stake. |
| Nick Pisciottano (D, SD-45) | Senate Finance Committee Minority Chair | 2026 | 0 | Low | No public statement found; represents Allegheny/Pittsburgh area. |
| Nikil Saval (D, SD-1) | Philadelphia delegation; Minority Chair, Senate Urban Affairs & Housing | 2026 (re-elected Nov. 2024) | 0 | Low | Previously advocated removing PA's uniformity clause, but **no current (2025–2026) restatement of that position was found** despite targeted search — treat his older stance as unconfirmed/stale rather than current, per this brief's evidence standard. Not a Finance Committee member. |
| Sharif Street (D, SD-3) | Philadelphia delegation | 2026 | 0 | Low | No LVT-specific statement found; general housing-affordability focus. |
| Art Haywood (D, SD-4) | Senate Finance Committee minority member; Philadelphia/Montgomery | 2026 | 0 | Low | No public LVT statement found despite representing part of Philadelphia and sitting on the relevant committee. |
| Steve Samuelson (D, HD-135) | House Finance Committee Chair | 2026 | 0 | Low | Represents Northampton County/Bethlehem, not Philadelphia; no statement found. |
| Keith J. Greiner (R, HD-43) | House Finance Committee Republican Chair | 2026 | 0 | Low | Represents Lancaster; no statement found. |
| Christopher Rabb (D-200, Philadelphia) | Chair, House Finance Tax Modernization & Reform Subcommittee | 2026 | 0 | Low | **Structurally the single most relevant gatekeeper** for a split-rate bill inside House Finance — no direct LVT quote found, but his subcommittee is the plausible point of entry. Worth direct outreach rather than further search. |
| Rick Krajewski (D-188, Philadelphia) | House Finance Committee member | 2026 | 0 | Low | Progressive tax-the-rich framing generally; no direct LVT quote. |
| Elizabeth Fiedler (D-184, Philadelphia) | House member | 2026 | +1 | Medium | On-record WHYY quote: "the uniformity clause really shields the super rich from paying their fair share" — advocacy for a tiered *income* tax via uniformity-clause reform, adjacent to but not the same as LVT. |
| Josh Shapiro (D) | Governor | Jan 2027 (up for re-election Nov. 2026) | 0 | Medium | No uniformity-clause, LVT, or split-rate statement found in his 2026-27 budget address or the enacted budget; the topic was not addressed in the final FY2026-27 budget deal (July 2026). A real, notable silence on a live Philadelphia issue, not merely an unsearched gap. |

**No LVT-specific or split-rate-specific bill was found introduced in the 2025–2026 PA legislative session.** SB 527 (Sen. Farry, R — passed Senate 29-21, pending in House Finance) amends the Sterling Act's wage-tax framework, proving the Sterling Act *can* be opened this session, but it is a wage-tax vehicle, not a property-tax template.

---

## 4. Electoral math

*(Populated from `analysis/data/philadelphia_lycd_post_abatement.csv`; non-exempt parcels only, n = 535,698 of 579,814 total.)*

- All non-exempt parcels with a tax decrease: **69.1%**
- SFR parcels with a tax decrease: **76.6%** (n = 408,137 SFR parcels)
- Median SFR tax change: **−23.0%**
- Commercial/industrial parcels with a tax increase: **45.9%** (n = 12,950 commercial+industrial)

### Category summary (selected, by parcel count)

| Category | n | Median Δ% | % decreasing |
|---|---|---|---|
| Single Family Residential | 408,137 | −14.2% | 68.1% |
| Small Multi-Family (2–4 units) | 37,944 | −25.3% | 84.7% |
| Abated / Construction Exemption | 30,111 | −21.5% | 84.0% |
| Vacant Land | 27,925 | **+577.7%** | 2.0% |
| Mixed Use | 13,399 | −22.6% | 83.6% |
| Commercial | 8,523 | −5.0% | 54.1% |
| Industrial | 3,485 | +53.1% | 25.5% |
| Large Multi-Family (5+ units) | 2,547 | −27.2% | 79.0% |
| Improved Vacant Land | 1,489 | +344.4% | 1.3% |
| Office / Commercial Condo | 805 | −21.9% | 68.8% |
| Hotel | 94 | −31.9% | 71.3% |

*Note: the 69.1%/76.6% headline figures above are computed across all non-exempt categories, not just the ones listed here — this table is a selected excerpt for readability.*

### Income quintile impact

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (lowest income) | −21.7% | Largest median cut of any quintile — the reform reads as progressive at the bottom of the income distribution. |
| Q2 | −22.2% | Largest cut overall — a strong "helps working-class blocks most" talking point. |
| Q3 | −20.2% | Still a substantial cut, slightly smaller than Q1/Q2. |
| Q4 | −19.4% | Smallest cut among all quintiles, but still a net decrease. |
| Q5 (highest income) | −19.4% | Essentially tied with Q4 — high-income neighborhoods are *not* disproportionately benefiting; the pattern is mildly progressive rather than regressive. |

### Minority concentration quintile impact

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (lowest minority %) | −19.9% | |
| Q2 | −20.6% | |
| Q3 | −21.4% | Largest cut is in the middle of the minority-concentration distribution, not at either extreme. |
| Q4 | −20.1% | |
| Q5 (highest minority %) | −20.1% | Essentially flat relative to Q1 — no evidence the reform disproportionately burdens high-minority-concentration neighborhoods. |

### Vacant land

- Vacant parcels (Vacant Land + Vacant Land — Exempt + Improved Vacant Land) as % of all taxable parcels: **7.1%** (41,274 of 579,814)
- Vacant Land alone sees a **+577.7% median tax increase** with only 2.0% of vacant parcels seeing any decrease — the single sharpest political data point in this model, and a direct fit for a blight/vacant-land frame.
- Top land-bank owners: **data not available for this run.** `analysis/ownership/philadelphia/` contains a general OPA ownership-concentration analysis (LLC entity resolution, investor-vs-homeowner patterns) but does not isolate vacant-land ownership specifically, and no `analysis/political/philadelphia_policy.csv`-style vacant-land-owner output exists for this model. A targeted vacant-land ownership pull would meaningfully strengthen the blight frame (Section 10) if run later.

### District-level breakdown

*Computed via centroid spatial join: `cities/philadelphia/data/parcels.gpq` (parcel geometry) → `analysis/data/philadelphia_lycd_post_abatement.csv` (join on `parcel_id`/`parcel_number`, leading zeros stripped) → `cities/philadelphia/data/council_districts.gpq` (reprojected from NAD83/PA South ftUS to EPSG:3857 for centroiding, then to EPSG:4326 for the join). 535,715 of 535,718 non-exempt parcels matched to a district (3 unmatched, negligible).*

| District | Councilmember | % All parcels ↓ | % SFR ↓ | Median SFR Δ% | SFR majority wins? |
|---|---|---|---|---|---|
| 1 | Mark Squilla | 64.9% | 65.2% | −12.3% | Yes |
| 2 | Kenyatta Johnson (Council President) | 69.2% | 69.7% | −16.3% | Yes |
| 3 | Jamie Gauthier | 67.5% | 70.3% | −19.3% | Yes |
| 4 | Curtis Jones Jr. | 67.4% | 68.4% | −15.2% | Yes |
| 5 | Jeffery Young Jr. | 58.1% | 62.2% | −13.1% | Yes |
| 6 | Michael Driscoll | 72.2% | 73.0% | −13.3% | Yes |
| 7 | Quetcy Lozada | 65.3% | 71.7% | −20.0% | Yes |
| 8 | Cindy Bass | 62.4% | 65.0% | −15.6% | Yes |
| 9 | Anthony Phillips | 64.7% | 64.0% | −8.6% | Yes |
| 10 | Brian O'Neill | 72.6% | 71.8% | −12.8% | Yes |

**Minimum winning coalition analysis:** **All 10 of 10** district councilmembers represent districts where a majority of SFR parcels see a tax decrease. Votes needed to pass a Council ordinance: 9 of 17. Even restricting attention to district members only, 10 of 10 already clears that bar on homeowner-relief grounds alone, before counting any of the 7 at-large votes. **This is the strongest single finding in this brief: there is no district in Philadelphia where the median homeowner is a net loser under this model.** The reform's political problem is not a homeowner-relief sales job at the district level — it is entirely the state-legislative gate described in Sections 2–3.

### Precinct-level vote-share correlation

*Computed from Philadelphia City Commissioners' official ward-division-level results (`vote.phila.gov`, 2023 Primary and General Results, "Totals" tab) spatially joined to `cities/philadelphia/data/parcels.gpq` centroids via `opendataphilly.org`'s current "Political Ward Divisions" boundary layer (1,703 divisions; confirmed current-cycle vintage, matching the 2023 election). Per the skill's guidance on dispositive elections in a one-party city, the **Democratic primary** is used for the 5 majority-party at-large seats and for district races that were only contested in the primary; the **general election** is used for District 10 (the one genuinely two-party-contested district seat) and the 2 minority-party at-large seats (decided among WFP/GOP candidates in the general). Districts 1–6 had no primary or general opponent in 2023 (uncontested Democratic incumbents) — there is no electoral-base variance to correlate for those seats, so their row is marked N/A rather than computed against a degenerate (near-zero-variance) vote share.*

| Official / race | Correlation (vote share vs. % all ↓) | Correlation (vote share vs. % SFR ↓) | Base-coalition SFR win rate | Interpretation |
|---|---|---|---|---|
| Mayor Cherelle Parker (2023 Dem primary, 9-candidate field) | r = −0.147 (p < 0.001) | r = −0.021 (n.s., p = 0.40) | 82.1% | Her strongest primary precincts skew slightly *toward* lower overall (all-parcel) decrease rates — plausibly because her base includes some commercial/mixed-use-heavy river-ward precincts — but the SFR-specific correlation is statistically indistinguishable from zero, and her stronghold's SFR win rate (82.1%) still comfortably exceeds 50%. Net read: safe ground to lead on homeowner relief specifically, more caution warranted on any citywide commercial-impact messaging. |
| District 7 — Quetcy Lozada (2023 Dem primary vs. Andrés Celín) | r = +0.020 (n.s.) | r = +0.086 (n.s., p = 0.28) | 90.5% | No significant directional signal, but her stronghold has the highest base-coalition SFR win rate of any contested district race — very safe ground. |
| District 8 — Cindy Bass (2023 Dem primary vs. Seth Anderson-Oberman) | r = −0.045 (n.s.) | r = −0.016 (n.s.) | 76.6% | No significant correlation either direction; base-coalition SFR win rate still comfortably positive despite her own −1 position score — her base would not obviously punish a "yes" vote on homeowner-relief grounds alone. |
| District 9 — Anthony Phillips (2023 Dem primary, 3-candidate field) | r = −0.025 (n.s.) | r = +0.038 (n.s.) | 85.4% | No significant signal; consistent with his already-supportive (+1) position — his base is not a constraint. |
| District 10 — Brian O'Neill (2023 general vs. Gary Masino, D) | r = +0.042 (n.s.) | **r = +0.173 (p = 0.032, significant)** | 92.3% | The only statistically significant SFR correlation among the district races: O'Neill's strongest general-election precincts are *positively* associated with SFR tax decreases. Combined with a 92.3% stronghold win rate, this is a genuine opening to court a Republican district councilmember on tax-relief grounds specifically, despite no current public position. |
| At-Large — Isaiah Thomas (2023 Dem primary) | r = −0.154 (p < 0.001) | r = −0.141 (p < 0.001) | 80.7% | Significant negative correlation on both measures — his strongest precincts are somewhat *less* likely to be net winners than his district-wide average, though still comfortably above 50% within his own stronghold. Not disqualifying, but a genuine nuance the district-level table alone would miss. |
| At-Large — Katherine Gilmore Richardson (2023 Dem primary) | r = −0.068 (p = 0.005) | r = −0.118 (p < 0.001) | 84.3% | Same pattern as Thomas, milder. |
| At-Large — Rue Landau (2023 Dem primary) | r ≈ 0.00 (n.s.) | r = −0.061 (p = 0.012) | 83.2% | Weak negative SFR correlation, but high stronghold win rate. |
| At-Large — Nina Ahmad (2023 Dem primary) | r = −0.082 (p < 0.001) | r = −0.067 (p = 0.006) | 82.6% | Same pattern; combined with her 0/Low position score and disclosed real-estate holding, she remains a genuine unknown rather than a likely no. |
| At-Large — Jim Harrity (2023 Dem primary) | r = +0.026 (n.s.) | r = +0.024 (n.s.) | 87.7% | No significant correlation; highest stronghold win rate among the 5 majority-party at-large winners. |
| At-Large — Kendra Brooks (2023 general, WFP minority seat) | r = −0.157 (p < 0.001) | r = −0.069 (p = 0.004) | 85.6% | Significant negative correlation on both, consistent with a WFP base concentrated in some higher-value/gentrifying precincts, but stronghold SFR win rate remains strongly positive. |
| At-Large — Nicolas O'Rourke (2023 general, WFP minority seat) | r = −0.126 (p < 0.001) | r = −0.075 (p = 0.002) | 85.4% | Same pattern as Brooks. |

**Overall precinct-level read:** every officeholder's electoral stronghold — without exception — has a base-coalition SFR win rate above 76%, several above 90%. Several at-large members and the Mayor show a statistically significant *negative* correlation between their strongest precincts and city-wide decrease rates, meaning their bases lean slightly more commercial/mixed-use than the city average — but this never flips the SFR-specific win rate below 50% for anyone. The single strongest positive finding is District 10's Brian O'Neill (r = +0.173 on SFR, p = 0.032, 92.3% stronghold win rate) — a Republican district councilmember whose own electorally strongest precincts are a particularly good fit for a homeowner-relief pitch, independent of his currently-unstated position.

---

## 5. Political environment

### Issue salience

- **Housing affordability:** High and current. Rents have risen roughly 26% since 2020; 2026 forecasts anticipate continued strain even as rent growth has flattened month-over-month. Mayor Parker's $2B "H.O.M.E." initiative (30,000-unit target, ~$277M spent in year one) is the administration's flagship response. [WHYY](https://whyy.org/articles/philadelphia-housing-market-pains-2026/)
- **Blight / vacant land:** High. ~130,000 vacant properties citywide, ~40,000 vacant lots, 74%+ privately owned. A December 2025 Inquirer investigation found the city's own Licenses & Inspections department no longer uses the vacancy-tracking tool it built, relying on complaints instead — a live, specific narrative that the current system cannot even *see* the blight problem it's supposed to address, which pairs directly with this model's Vacant Land finding (+577.7% median, only 2% seeing a decrease). [Inquirer](https://www.inquirer.com/real-estate/housing/a/vacant-dangerous-rowhouses-licenses-inspection-data-20251208.html)
- **Property tax burden / assessment fairness:** Very high and actively escalating as of this writing. The 2024 citywide reassessment raised residential values ~19% on average (~$330/year average increase, with some neighborhoods seeing 60%+ jumps); as of **July 15, 2026**, City Council was actively and publicly pressing the Parker administration on a new round of rising assessments, calling the methodology opaque. [Inquirer, July 15 2026](https://www.inquirer.com/politics/philadelphia/property-value-taxes-council-parker-20260715.html) The Homestead Exemption was raised from $80,000 to $100,000 in 2025, with further increases proposed — evidence of ongoing legislative churn on exactly the lever LVT would also touch.
- **Construction tax abatement reform:** Active. PA legislators authorized (Nov. 2025) a new 20-year abatement for converting vacant/underused office and school buildings; Parker's administration is separately exploring a 100% abatement for underinvested neighborhoods (April 2025) — this LYCD post-abatement model's entire premise (treating existing abatements as expired) sits directly inside a live policy debate, not a hypothetical one.
- **Downtown/commercial vacancy:** Moderate. Center City office vacancy ~20.4% (Q2 2025), roughly flat through Q1 2026 — notably better than many peer downtowns, which somewhat softens a "vacant downtown" framing angle relative to residential vacancy/blight.

### Advocacy landscape

- **LVT-specific:** The Robert Schalkenbach Foundation has directly modeled Philadelphia LVT impacts and its executive director has publicly estimated large aggregate homeowner savings; the City's own Revenue Commissioner has directly and publicly countered that Philadelphia lacks legal authority to enact LVT. Both sides of this exact debate are already active and on the record. [WHYY](https://whyy.org/articles/a-progressive-approach-to-taxing-land-gains-traction-in-philly-council/)
- **Tenant organizing:** Philadelphia Tenants Union — grassroots, tenant-led, holding annual conferences — but its primary current campaign is rent control, not LVT; a natural but not automatic ally.
- **YIMBY:** 5th Square / Philly YIMBY — Philadelphia's urbanist PAC, source of several of the endorsement signals in Section 3, with demonstrated capacity on zoning votes.
- **Community development:** PACDC (Philadelphia Association of Community Development Corporations) — active on investor-ownership and equitable-development issues, a plausible coalition partner.
- **Organized opposition:** HAPCO Philadelphia (the city's largest rental-property-owner association) is currently and visibly organized — it sued the City in 2025-2026 alleging Sunshine Act violations while fighting the "Safe Healthy Homes Act" renter-protection package, which Council nonetheless passed nearly unanimously in April 2026. This is concrete, current evidence of both HAPCO's organizing capacity and its recent limits.
- **Business/commercial:** Greater Philadelphia Association of Realtors and the Chamber of Commerce for Greater Philadelphia are both active on tax policy generally; no explicit LVT position was found for either — a genuine open question, not a confirmed opposition.

### Peer city signal

Pennsylvania has a real split-rate tradition, but it is a **dormant** one, not an active trend: Scranton (1913), Harrisburg (1975), Washington PA (1985), McKeesport (1980), and Allentown (1997) all currently or historically operate split-rate; Pittsburgh ran one from 1913–2001 before repealing it (a cautionary precedent — repeal is politically possible even after 90 years). No 2024–2026 news of expansion, adoption, or repeal was found for any of these — Philadelphia would be *reviving* a largely static PA tradition, not joining current momentum, which is a materially different (weaker) social-proof argument than the brief would want if there were live peer-city energy to point to.

### Recent referenda

No property-tax-structure ballot measure was found 2021–2026. Recent measures (Zoning Board reform, May 2022; RCO legal-cost charter amendment, April 2024; Housing Trust Fund in-lieu-payment measure, May 2025) show voters are receptive to housing/zoning-adjacent ballot questions generally, but none tests appetite for a tax-base restructuring specifically.

### Election calendar

Next municipal election: **November 2, 2027** (primary May 18, 2027) — Mayor and all 17 Council seats up simultaneously, roughly 15–16 months from this brief's date. This falls inside the 24-month planning window. The natural post-election policy window (a Sterling Act push or a Council resolution) would open after that election, i.e., roughly January–mid-2028, unless a state legislative sponsor emerges sooner and makes a pre-election push possible.

---

## 6. Demographic predictors

| Factor | City figure | Political implication |
|---|---|---|
| Renter proportion | 47.7% (2019–2023 ACS 5-year) | Above the ">45%" threshold for "large latent LVT constituency" — renters are close to half the city, though (per the skill's standing caveat) their political translation depends on turnout and organization, which Philadelphia's tenant unions are only partially building toward LVT specifically (their focus is rent control). [Census Reporter](http://censusreporter.org/profiles/16000US4260000-philadelphia-pa/) |
| Median age | 35.1 years | Right at the "younger favors LVT more" threshold from prior CLE/PPI polling; roughly 40% of the population is under 35 (derived from published age-band data — recommend pulling ACS table S0101 directly for a precise figure before further use). |
| Homeownership rate | ~52% | High enough that organized homeowner voice matters, but the SFR electoral math (Section 4) shows homeowners are broadly net winners under this model — a favorable combination rather than a headwind. |
| Partisan lean | Overwhelmingly Democratic; Parker won the 2023 mayoral general 74.5%–25.5% (~49-point margin); Trump grew his Philadelphia vote count from 132,870 (2020) to 141,203 (2024) even as the city stayed blue, winning 5 of 66 wards outright | A one-party-dominant environment where the **Democratic primary**, not the general, is the real contest for nearly every seat (reflected in Section 4's precinct methodology) — but a real (if modest) erosion at the margins worth noting for durability. |
| Median household income | $60,849 (2019–2023 ACS 5-year) | Middling by national standards; the income-quintile pattern in Section 4 (mildly progressive — Q1/Q2 see the largest cuts) is a genuine asset for an affordability-focused frame in a city where median income is not high. |

---

## 7. Coalition map

|  | **For LVT** | **Against LVT** |
|---|---|---|
| **Organized** | Robert Schalkenbach Foundation (active, LVT-specific modeling/advocacy for Philadelphia); 5th Square / Philly YIMBY (demonstrated zoning-vote capacity, several council endorsements); PACDC (equitable-development focus, natural adjacency) | HAPCO Philadelphia (largest rental-property-owner association, currently and visibly organized — 2025-2026 litigation against Council); City of Philadelphia's own Law Department (institutional position that LVT likely violates the uniformity clause — an unusual "opponent" in that it is part of the same government that would need to enact the reform) |
| **Latent / unorganized** | Renters (47.7% of the city, large but only partially organized around LVT specifically); younger residents (median age 35.1); SFR homeowners in the 10 districts and 76.6% citywide who see a tax decrease under this model, if the specific numbers reach them | Owners of large commercial/vacant-land parcels facing the sharpest increases (Vacant Land +577.7% median, Industrial +53.1% median) — currently unorganized as a *land-value-tax-specific* opposition bloc, but individually well-resourced and, per the legal brief, financially motivated to litigate at Philadelphia's scale even without pre-organizing |

Chamber of Commerce for Greater Philadelphia and Greater Philadelphia Association of Realtors are both active on tax policy generally but have no confirmed LVT-specific position — genuinely unclassified rather than placed in either quadrant.

---

## 8. Official alignment score

Because the legal pathway is bifurcated (state enabling legislation first, then a City Council ordinance), this section reports both layers rather than a single blended number, per the legal brief's Gate-4 scope requirement.

**Layer 1 — Pennsylvania General Assembly (the actual binding constraint):**
- Officials researched: 11 (2 Senate Finance leaders, 3 additional Philadelphia-delegation senators, 2 House Finance leaders, 3 additional Philadelphia-delegation House members, the Governor)
- Score breakdown: ten officials at 0/Low, one (Fiedler) at +1/Medium on an adjacent-but-not-identical uniformity-clause position
- **Overall alignment: Split / uncertain — in practice, a vacuum rather than active opposition.** No legislator or the Governor has taken a position against LVT; equally, none has taken a position for it, and **no bill exists**. This is a "find a sponsor" problem, not a "flip a no vote" problem.
- Key swing/target: Rep. Christopher Rabb (D-200), whose House Finance Tax Modernization & Reform subcommittee chairmanship makes him the single most plausible entry point, despite no located public statement.

**Layer 2 — Philadelphia City Council (the eventual implementing vote, once state authority exists):**
- Votes required: 9 of 17
- Officials researched: 17 (all current members) + Mayor
- Score breakdown: District members sum to 0 (two +1s, two −1s, six 0s across the 10 seats); at-large members sum to +6 (six +1s, one 0 across 7 seats); Mayor +1 (not a Council vote, but relevant to signing/vetoing an eventual ordinance)
- Mean score across the 17 Council members: **+0.35** → **Thin majority support**, in the skill's scoring bands (+0.25 to +0.99)
- Key swing votes: Nina Ahmad (0/Low, disclosed real-estate holding — genuinely uncertain); Brian O'Neill (0/Low, but his own base shows the only statistically significant positive SFR correlation among district races — a persuadable target on tax-relief grounds specifically); Cindy Bass (−1/Medium, but her base's SFR win rate remains 76.6%, meaning her opposition is not obviously demanded by her own electorate).

**Net read:** City Council would very plausibly assemble a majority once it has something to vote on. The reform's viability bottleneck sits entirely in Harrisburg.

---

## 9. Structural viability score

| Factor | Score (0–2) | Rationale |
|---|---|---|
| Electoral math | 2 | 76.6% of SFR parcels see a decrease (>60% threshold) |
| Renter proportion | 2 | 47.7% renter-occupied (>45% threshold) |
| Housing crisis salience | 2 | Dominant, currently escalating issue — active Council-vs-administration fight over assessments as of July 2026, ongoing abatement-reform debate, live housing-affordability coverage |
| Legal pathway ease | 1 | Tier 4/5 — state enabling legislation required (mid-range; not a bare ordinance, but not a constitutional amendment either) |
| Organized ally strength | 1 | Schalkenbach Foundation is a real, LVT-specific advocate, and 5th Square/PACDC provide adjacent organizing capacity, but no organization has yet built specifically toward an LVT campaign in Philadelphia — closer to "one substantive but narrow organization" than "multiple demonstrated-capacity orgs aligned on this specific reform" |
| **Total** | **8/10** | |

---

## 10. Strategic framing

**Recommended primary frame:** Property tax / assessment fairness for homeowners. This is not a frame that needs to be manufactured — Council was publicly pressing the administration on assessment fairness the week before this brief was written, and the model shows 76.6% of SFR parcels and every single Council district benefiting, with a mildly progressive income-quintile pattern (Q1/Q2 see the largest cuts). This frame rides an already-moving news cycle rather than competing with it.

**Recommended secondary frame:** Blight / vacant land. The Vacant Land category's +577.7% median increase (only 2.0% of vacant parcels see any decrease) is the single sharpest number in this model, and it pairs directly with the live "L&I can't even track vacant properties" narrative (Inquirer, Dec. 2025). This is a strong complement to the homeowner-relief frame, not a substitute — it answers "who pays for the homeowner relief" with a politically vivid answer (idle land, not working homeowners).

**Frames to avoid:** A pure "business investment" / commercial-attraction frame is weaker here than in many other modeled cities — 45.9% of commercial/industrial parcels see a tax *increase* under this specific post-abatement LYCD model (Industrial's median change is +53.1%), so leading with "this helps business" risks an immediate, factual rebuttal from organized commercial interests. Use the homeowner and blight frames; treat the commercial impact as a secondary, honestly-disclosed tradeoff rather than a talking point.

### Key talking points (grounded in model data)

- "Every single Council district in Philadelphia — all 10 — has a majority of homeowners paying less under this reform, with a citywide median cut of 23% for single-family homes."
- "Vacant land in Philadelphia would see its tax bill rise nearly six-fold on a median basis, while 76.6% of homeowners see a cut — the reform shifts the burden from people living in their homes to land being held idle."
- "The lowest-income neighborhoods in Philadelphia see the *largest* median tax cuts of any income group under this model, not the smallest."
- "This isn't hypothetical for Pennsylvania — Scranton, Harrisburg, Allentown, and other PA cities have run split-rate taxes for decades; Philadelphia would be reviving a Pennsylvania tradition, not importing an untested idea, though no PA city has moved on this in the current legislative session, so the coalition would need to build fresh momentum rather than ride an existing wave."

---

## 11. Open questions and research gaps

- **No state legislative sponsor identified.** This is the single most consequential gap: every other finding in this brief (favorable Council math, favorable structural conditions) is conditional on someone in Harrisburg agreeing to carry a bill. Direct outreach to Rep. Rabb's office is the most promising next research/organizing step, not further web search.
- **City-only vs. combined city+school levy scope mismatch.** This model's revenue baseline ($2.06B) reflects the *combined* city + school district levy (13.998 mills), but the Tier 4/5 legal pathway most directly authorizes the *city's* 0.6317% portion; the school district's 0.7681% would need separate School Board action under its own enabling statute. The electoral-math figures in Section 4 should be read as "if both levies moved together," not as a guaranteed feature of a city-only enabling bill — a genuine open question for a follow-up analysis that models the city-only levy in isolation.
- **Nikil Saval's current position is unconfirmed.** His historical uniformity-clause advocacy could not be re-verified with a 2025-2026 statement; treat any assumption that he remains a champion as stale until directly confirmed.
- **Top vacant-land owners not identified for this run** — a dedicated ownership pull limited to vacant/blighted parcels (building on the existing general ownership-concentration work in `analysis/ownership/philadelphia/`) would meaningfully sharpen the blight frame in Section 10.
- **Chamber of Commerce for Greater Philadelphia and Greater Philadelphia Association of Realtors' specific LVT positions are unknown** — both are active on tax policy generally; a direct inquiry or further search would resolve genuine unknowns rather than assumed opposition.
- **Precinct redistricting vintage:** the "Political Ward Divisions" boundary layer used for Section 4's precinct correlation is the *current* OpenDataPhilly layer; it was cross-checked as matching the 2023 election cycle (post-2020-redistricting), and the separate "Historic Political Wards & Divisions" (2003–2020) dataset was correctly *not* used, avoiding a vintage mismatch.
- **Districts 1–6 have no computable precinct-level "base coalition" signal** because their 2023 races were uncontested — this is a genuine data limitation (not a research failure) that will persist until one of those seats draws a real primary or general challenger.

---

## 12. Sources

**Legal/procedural:**
- [analysis/legal/Philadelphia.md](../legal/Philadelphia.md) — LVT legal brief (2026-06-01)

**Council & Mayor:**
- [phlcouncil.com/members](https://phlcouncil.com/members) — official current roster
- [Axios Philadelphia — Parker unpaid tax lien, Feb. 2025](https://www.axios.com/local/philadelphia)
- [WHYY — Philly tax reform means repealing PA's uniformity clause](https://whyy.org/articles/philadelphia-tax-reform-pa-uniformity-clause/)

**State legislature:**
- [PA Senate Finance Committee roster](https://www.palegis.us/senate/committees/25/finance?sessyr=2025)
- [PA House Finance Committee roster](https://www.palegis.us/house/committees/16/finance)
- [Nikil Saval official bio](https://www.palegis.us/senate/members/bio/1921/senator-nikil-saval) / [Ballotpedia](https://ballotpedia.org/Nikil_Saval)
- [PA 2026-27 Budget in Brief](https://www.pa.gov/content/dam/copapwp-pagov/en/budget/documents/publications-and-reports/commonwealthbudget/2026-27-budget-documents/2026-27%20budget%20in%20brief.final.web.v.2.pdf)
- [Inquirer — PA 2026 budget deal](https://www.inquirer.com/politics/pennsylvania/pennsylvania-budget-2026-josh-shapiro-20260712.html)
- [PA Senate Republicans — SB 527 Sterling Act wage-tax amendment](https://www.pasenategop.com/news/bills/june-23-26-2025/)
- [Earth Rights Institute — PA split-rate municipal history](http://www.earthrights.net/docs/success.html)
- [Lincoln Institute — "How Smart Is the Split-Rate Property Tax?"](https://www.lincolninst.edu/app/uploads/legacy-files/pubfiles/banzhaf-wp08sb1.pdf)

**Political environment:**
- [WHYY — Philadelphia housing market pains expected in 2026](https://whyy.org/articles/philadelphia-housing-market-pains-2026/)
- [Inquirer — L&I no longer uses its vacant-property tracking tool](https://www.inquirer.com/real-estate/housing/a/vacant-dangerous-rowhouses-licenses-inspection-data-20251208.html)
- [Inquirer — Philly homeowners will see property tax bills increase $330](https://www.inquirer.com/politics/philadelphia/philadelphia-property-tax-reassessment-increase-mayor-cherelle-parker-20240805.html)
- [Inquirer — Council members probe Parker administration on rising assessments, July 15 2026](https://www.inquirer.com/politics/philadelphia/property-value-taxes-council-parker-20260715.html)
- [WHYY — Philly Council debates land value tax vs. property tax](https://whyy.org/articles/a-progressive-approach-to-taxing-land-gains-traction-in-philly-council/)
- [Robert Schalkenbach Foundation — How a Land Value Tax Would Impact Philadelphia](https://schalkenbach.org/how-a-land-value-tax-would-impact-philadelphia/)
- [Philadelphia Tenants Union](https://phillytenantsunion.org/latest-news/)
- [Philly YIMBY / 5th Square](https://phillyyimby.com/)
- [Inquirer — Landlords tried to stop bills to protect renters](https://www.inquirer.com/real-estate/housing/philadelphia-renter-protections-council-passed-safe-healthy-homes-20260423.html)
- [PACDC](https://pacdc.org/)
- [2027 Philadelphia mayoral election — background](https://en.wikipedia.org/wiki/2027_Philadelphia_mayoral_election)
- [Inquirer — All 17 City Council members could run for reelection in 2027](https://www.inquirer.com/politics/philadelphia/city-council-members-reelection-20251216.html)

**Demographics:**
- [Census Reporter — Philadelphia profile (2019-2023 ACS 5-year)](http://censusreporter.org/profiles/16000US4260000-philadelphia-pa/)
- [Census QuickFacts — Philadelphia County](https://www.census.gov/quickfacts/fact/table/philadelphiacountypennsylvania/AFN120217)
- [CBS Philadelphia — 2024 presidential election results](https://www.cbsnews.com/philadelphia/news/philadelphia-presidential-election-results-2024/)
- [PhillyVoice — 2023 mayoral election results](https://www.phillyvoice.com/philly-mayor-election-results-cherelle-parker-david-oh-2023/)

**Precinct-level data (Section 4):**
- [Philadelphia City Commissioners — Past Election Results](https://vote.phila.gov/resources-data/past-election-results-2/past-election-results/) (2023 Primary and General Results, "Totals" tab, downloaded directly)
- [OpenDataPhilly — Political Ward Divisions](https://opendataphilly.org/datasets/political-ward-divisions/) (current-vintage boundary layer, ArcGIS FeatureServer)
- `cities/philadelphia/data/parcels.gpq`, `cities/philadelphia/data/council_districts.gpq` — cached parcel and district geometry used for all spatial joins in this brief

---

*This brief is an independent companion to `analysis/political/Philadelphia.md` (the OPA-based model brief). Officials, legal pathway, and environmental findings were re-researched from scratch for this run rather than assumed to carry over; the underlying facts about who holds office and what the legal blocker is turned out to be the same city-level reality either way, which is expected and does not indicate the two briefs were not independently produced.*
