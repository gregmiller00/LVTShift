# Richmond, Virginia — LVT Political Viability Brief

**Date of analysis:** 2026-06-03  
**Overall viability:** Tier 2 — Achievable  
**Official alignment:** Split / uncertain (mean score +0.22/9 council members; 3 lean-yes, 1 lean-no, 5 unknown; majority not yet assembled)  
**Structural viability score:** 8/10  
**Legal pathway (from brief):** City council ordinance under existing state authority — Va. Code §58.1-3221.1 explicitly names Richmond. No new legislation needed. Simple majority (5 of 9 council members) after one public hearing.  
**Model type (from export):** split_rate:4.0 — 4:1 land-to-improvement ratio, revenue-neutral at $526M

---

## 1. Summary

Richmond has the legal authority, the structural conditions, and nascent political support to implement LVT by city council ordinance — but as of June 2026 has not acted despite having held the legal authority since 2020. The underlying conditions are strong: 56.5% renter rate, dominant housing affordability salience, an active YIMBY chapter with recent wins, and a Tier 1 legal pathway. The structural viability score is 8/10.

The gap is the council majority. The critical constraint revealed by the district-level model analysis is that **only 3 of 9 districts have an SFR homeowner majority that benefits** under a 4:1 split-rate (Districts 4, 8, and 9). A coalition built primarily on homeowner tax relief cannot cross the 5-vote threshold — it falls two votes short. The winning coalition must instead lead with the **blight/vacant land** and **housing production** frames, which appeal across districts regardless of homeowner win/loss status, and use homeowner relief as the district-specific close in the three favorable districts.

**Top 2 risks:** (1) Organized commercial real estate opposition — 78% of commercial/industrial parcels see tax increases, and the Virginia Realtors and VAMA have track records opposing reform in Richmond; (2) Equity optics — the income quintile pattern shows lower-income block groups have higher mean tax changes (driven by vacant and commercial parcels, not SFR homeowners), and this can be weaponized by opponents.

**Top opportunity:** The Code Refresh zoning overhaul is coming to council in spring 2026. LVT + Code Refresh is a natural pairing — LVT penalizes land-hoarding and rewards development, directly complementing density reform. A councilmember who already supports the Code Refresh has a coherent political narrative for supporting LVT.

**What would most change this assessment:** An explicit public statement from Mayor Avula endorsing revenue-neutral LVT as the city's "targeted tax relief" alternative to a flat rate cut. His own framing — "targeted reduction that actually helps the most vulnerable" — maps directly onto LVT's redistributive mechanics, and a mayoral endorsement would likely move 2–3 neutral council members.

---

## 2. Prerequisites Consumed

**Legal brief:** Present — `analysis/legal/richmond.md`
- Pathway: Vehicle A direct split-rate, Tier 1 (city council ordinance alone)
- Required votes: 5 of 9 council members; public hearing under §58.1-3007 (no referendum required)
- Levies in scope: City levy only (Richmond is an independent city; $1.20/$100 covers all operations)

**Model export:** Present — `analysis/data/richmond.csv`
- Model type: split_rate:4.0 (land taxed at 4× improvement rate, revenue-neutral)
- Parcel count: 76,879 (72,340 taxable)
- Current revenue (modeled): ~$526M gross levy; ~$494M net collections (FY2025)
- Key stats: 47.5% of all taxable parcels see a decrease; 51.2% of SFR parcels see a decrease; median SFR change -0.48%; 78.3% of commercial/industrial parcels see an increase

**District computation:** Computed — council district boundaries fetched from Richmond GeoHub (FeatureServer: `services1.arcgis.com/k3vhq11XkBNeeOfM/arcgis/rest/services/CouncilDistricts/FeatureServer/0`). Spatial join of 76,879 parcel centroids to 9 districts, per-district SFR stats recomputed from GeoParquet.

---

## 3. Political Actors

**Current-service verification:** Confirmed against [rva.gov/richmond-city-council/council-contacts](https://www.rva.gov/richmond-city-council/council-contacts) and RVAHub oath-of-office article (Jan 3, 2025). All 9 members below are serving the 2025–2028 term.

| Name | Role | Term ends | Electoral base | District wins? | Score | Conf | Key evidence |
|---|---|---|---|---|---|---|---|
| **Cynthia Newbille** | Council President, D7 East End | Dec 2028 | Majority-minority, highest eviction rate in city, renter-heavy | NO (47.1% SFR) | 0 | L | No LVT statement found. Voted to maintain $1.20 rate (with Avula). Said "all council members want to reduce the tax rate" but not the right moment. |
| **Katherine Jordan** | Vice President, D2 N. Central | Dec 2028 | Mixed residential/commercial near Museum District | NO (29.7% SFR) | -1 | L | Voted to maintain rate citing Trump uncertainty; fiscally cautious framing suggests skepticism of novel tax structure. [VPM Nov 2024](https://www.vpm.org/news/2024-11-12/richmond-council-votes-real-estate-tax-rate-nye-trammel) |
| **Kenya Gibson** | Member, D3 Northside | Dec 2028 | Northside, mixed residential, affordability-focused | NO (42.6% SFR) | 0 | L | Strong housing affordability advocate; wrote Code Refresh analysis. Concerned about HUD AMI definitions favoring market-rate development. No LVT statement found. [Medium essay on Code Refresh](https://kenya-gibson.medium.com/considerations-for-the-code-refresh-zoning-the-richmond-we-want-to-build-da2940f39d4d) |
| **Sarah Abubaker** | Member, D4 Southwest | Dec 2028 | Southwest suburbs, homeowner-heavy, mostly SFR | YES (78.4% SFR) | +1 | M | Voted for 4-cent property tax rate cut in Oct 2025 alongside Lynch and Trammell. Consistent homeowner-relief advocacy. District has 2nd-highest SFR win rate. [The Richmonder Oct 2025](https://www.richmonder.org/siding-with-avula-council-rejects-push-to-lower-real-estate-tax-bills/) |
| **Stephanie Lynch** | Member, D5 Central | Dec 2028 | Mixed urban, VCU/Carytown corridor, renter-heavy | NO (33.1% SFR) | +1 | M | Reported support for "exploring alternatives such as a land value tax as part of economic development strategy" (Richmond Together 2024 questionnaire). Voted for 4-cent rate cut. [Richmond Together](https://www.richmondtogether.org/p/stephanie-lynch-5th-district-city.html) |
| **Ellen Robertson** | Member, D6 Gateway | Dec 2028 | Southern/Gateway area, mixed suburban | NO (41.7% SFR) | 0 | L | No LVT or property tax position statement found. Voted with majority on Housing Trust Fund restitution matter (Sep 2025). |
| **Andrew Breton** | Member, D1 West End | Dec 2028 | Upper-income West End, high land values relative to improvements | NO (32.5% SFR) | 0 | L | No clear property tax position found for 2024-2025. District economics are the most unfavorable in the city for SFR homeowners under LVT. |
| **Reva Trammell** | Member, D8 Southside | Dec 2028 | Southside, working-class homeowners, very SFR-heavy | YES (53.2% SFR) | +1 | M | Proposed 4-cent property tax rate cut (2024); voted for it in Oct 2025. Explicitly said "I'm tired of people saying 'What is a few little dollars?'" about homeowner burden. [The Richmonder](https://www.richmonder.org/as-home-values-rise-again-trammell-proposes-lowering-richmonds-property-tax-rate/) |
| **Nicole Jones** | Member, D9 S. Central | Dec 2028 | Southside, very homeowner-heavy SFR neighborhoods | YES (84.4% SFR) | 0 | L | New member (Jan 2025). No public property tax position found. District has the highest SFR win rate in the city — strongest potential persuasion target. |

**Mayor Danny Avula** (elected Nov 2024, inaugurated Jan 2025; 4-year term):
- Role: Sets agenda; no council vote, but mayoral endorsement carries significant weight with uncertain members.
- Position: Opposed flat property tax rate cut as inequitable. Said: "A more targeted reduction that actually helps that population is what we should be working to craft, as opposed to something that goes across the board." This framing aligns precisely with LVT's redistributive mechanics — revenue-neutral LVT is exactly the "targeted" alternative his framing implies.
- Score: +1 (inferred — no direct LVT statement; reasoning is LVT-consistent), Confidence: Medium
- [The Richmonder](https://www.richmonder.org/nows-not-the-time-to-cut-richmonds-property-taxes-avula-says/)

---

## 4. Electoral Math

- All taxable parcels with tax decrease: **47.5%** — slightly under half; tells us the typical taxable parcel does not benefit, driven by commercial and vacant land parcels with large increases
- SFR parcels with tax decrease: **51.2%** — a bare majority of homeowners benefit; politically defensible city-wide but not in most districts
- Median SFR tax change: **-0.48%** — very small median decrease; not a dramatic homeowner benefit talking point
- Commercial/industrial parcels with tax increase: **78.3%** — strong organized opposition signal; most commercial properties lose under 4:1

### Income Quintile Impact

| Quintile | Mean tax change % | Political reading |
|---|---|---|
| Q1 (lowest income BGs) | +14.66% | Caution: lower-income neighborhoods show highest mean increase, driven by vacant lots and commercial parcels in those areas — not SFR homeowners. Opponents will cite this; requires active rebuttal. |
| Q2 | +12.84% | Same dynamic. |
| Q3 | +11.39% | Moderate-income areas also net positive mean on average. |
| Q4 | +10.67% | |
| Q5 (highest income BGs) | +8.25% | High-income areas (more improved land) see smallest mean increase. |

**Important caveat on income quintiles:** These are mean tax changes at the parcel level, averaged across ALL parcel types in each block group. The mean is pulled up by large increases on vacant land and commercial parcels, which are disproportionately located in lower-income areas. The median SFR change is negative city-wide (-0.48%), and the SFR homeowner majority-wins analysis (Section 4 district table) shows the individual-homeowner story is more nuanced. Opponents will cite the block-group mean; advocates should lead with the SFR median and the vacant-land penalty as the corrective narrative.

### Minority Concentration Quintile Impact

| Quintile | Mean tax change % | Political reading |
|---|---|---|
| Q1 (least minority BGs) | +9.40% | |
| Q2 | +12.03% | |
| Q3 | +10.28% | |
| Q4 | +11.55% | |
| Q5 (most minority BGs) | +17.56% | Highest minority-concentration block groups show highest mean increase — same vacant-lot/commercial dynamic. Must be proactively addressed: the anti-speculation vacant land penalty disproportionately affects speculative land bankers operating in communities of color, and forcing development reduces blight in those neighborhoods. |

### Vacant Land

- Vacant parcels as % of all taxable: **7.3%** (5,275 parcels)
- Median vacant land tax change: +119.1%
- Top land-bank owners: not available in model export. Research needed to identify the largest vacant land holders by acreage; institutional or corporate holders make the strongest political messaging targets.

### District-Level Breakdown

| District | Councilmember | % All parcels ↓ | % SFR ↓ | Median SFR Δ% | SFR majority wins? |
|---|---|---|---|---|---|
| 1 | Breton (West End) | 36.1% | 32.5% | +7.0% | NO |
| 2 | Jordan (N. Central) | 35.8% | 29.7% | +7.0% | NO |
| 3 | Gibson (Northside) | 41.1% | 42.6% | +2.6% | NO |
| 4 | Abubaker (Southwest) | 74.5% | 78.4% | -7.9% | **YES** |
| 5 | Lynch (Central) | 32.9% | 33.1% | +8.5% | NO |
| 6 | Robertson (Gateway) | 42.6% | 41.7% | +3.0% | NO |
| 7 | Newbille (East End) | 46.5% | 47.1% | +0.7% | NO |
| 8 | Trammell (Southside) | 45.3% | 53.2% | -1.1% | **YES** |
| 9 | Jones (S. Central) | 78.0% | 84.4% | -9.2% | **YES** |

**Minimum winning coalition analysis:** 3 of 9 districts have SFR majority wins — fewer than the 5 votes needed for passage. A pure homeowner-relief framing cannot carry a majority coalition. The 2 swing votes needed beyond Abubaker/Trammell/Jones must come from districts where SFR homeowners do not have majority wins (D3, D6, D7). For those members, the blight/vacant-land and housing-production frames must carry the argument.

Note: District 7 (Newbille, 47.1%) is closest to the break-even. With 47.1% of SFR parcels winning, Newbille's East End is nearly split. Combined with the district's acute housing crisis and eviction burden, the anti-speculation/vacant-land frame is plausible there.

Note on Lynch (D5): Lynch's district shows only 33.1% SFR wins, yet she has reportedly expressed LVT interest. This confirms that the housing-production and blight frames (not homeowner relief) are what motivate her interest — consistent with her broader housing-affordability agenda.

---

## 5. Political Environment

### Issue Salience

**Housing affordability — HIGH.** Richmond has one of the highest eviction rates of any U.S. city with over 100,000 people, consistently ranking #2 nationally. The housing affordability crisis has been a dominant council and mayoral campaign theme through 2023–2025. By 2024, a Richmond household needed $122,866 to afford the $410,000 median home price. The council declared a "public crisis" on evictions in September 2024. Mayor Avula's FY2027 budget dedicates over $25 million to housing, including $11.7M for the Affordable Housing Trust Fund. This is the single most powerful frame for LVT.

**Vacant land and blight — MODERATE.** Richmond has 5,275 vacant taxable parcels (7.3% of the taxable base). The city's Code Refresh rezoning process specifically identified underutilized land as a constraint on housing production. The Virginia Mercury (2023) directly cited LVT as a mechanism to address vacant land hoarding. The connection between speculative land-banking and housing scarcity is an established part of local discourse — LVT's vacant-land penalty is politically pre-framed.

**Property tax homeowner burden — MODERATE.** The October 2025 property tax vote showed real council energy on homeowner tax relief, with Abubaker, Lynch, and Trammell explicitly proposing a rate cut. Property tax increases from rising assessments have generated constituent complaints. This is the frame for Districts 4, 8, and 9 but does NOT extend to the other 6 districts.

**Code Refresh zoning — HIGH (window).** Richmond's comprehensive zoning rewrite is scheduled for a council vote in spring 2026. This creates an explicit political window: LVT + dense zoning is a coherent package where LVT provides the land-price signal that makes infill development viable even after zoning allows it. Any councilmember who supports the Code Refresh has a coherent narrative for also supporting LVT.

### Advocacy Landscape

**RVA YIMBY** (active, capacity demonstrated): Richmond chapter of YIMBY Action. Founded March 2023. Won unanimous council votes on parking minimum elimination and ADU by-right zoning. Led by Joh Gehlbach. Has demonstrated legislative capacity and council relationships. Does not currently have LVT as a stated priority but is the natural ally organization — their mission (abundant, affordable, accessible housing) maps exactly onto LVT's anti-speculation goals. Approach: brief RVA YIMBY leadership on LVT's housing-production mechanics and offer district-level model data as an organizing tool.

**Richmond Tenants Union** (nascent, capacity unclear): Exists with copyright 2025 on its website but limited public activity found. If it becomes active, represents the renter constituency that most directly benefits from LVT (lower land costs → competitive pressure on rents over time).

**Better Housing Coalition** (established, nonprofit): Affordable housing developer and advocacy org. Administers programs for lower-income homeowners and renters. Has council relationships. Worth engaging on MWCLT concerns (72 CLT parcels face higher land taxes under LVT — needs policy carve-out or explicit framing).

**Virginia Apartment Management Association / Virginia Realtors** (organized opposition): Both organizations opposed Richmond rent stabilization legislation in recent years and testified in Richmond. They are the most likely organized opposition to LVT on the grounds of commercial property tax increases. Neither has staked a position specifically on split-rate/LVT yet.

### Peer City Signal

None of the four originally-authorized Virginia cities (Fairfax, Poquoson, Richmond, Roanoke) have enacted LVT despite having had the authority since 2002–2020. This "none have done it yet" status cuts two ways politically: there is no precedent to point to within Virginia, but the 2026 HB 282 expansion to four more cities (passed 91-8) shows strong legislative momentum. Richmond could be the first mover and demonstrate for Charlottesville, Falls Church, Fredericksburg, and Newport News. The University of Richmond Public Interest Law Review published an analysis of LVT's potential for affordable housing in Richmond in 2022 — local academic backing for the idea exists.

### Recent Referenda

No directly relevant ballot measures in the last 5 years. The October 2025 property tax vote (council vote, not a referendum) is the closest analogue — showing that tax reform is live and contested but that the reform coalition (3 votes for the rate cut) is short of a majority without new persuasion.

### Election Calendar

All 9 council members and Mayor Avula were sworn in January 2025 and serve until December 2028. **The next 3+ years are all post-election window** — the maximum policy-action period in any council cycle. There is no imminent election risk for any council member until 2028. This is the strongest argument for near-term action: the political cost of a novel vote is lowest immediately after an election, and the council is fully 3+ years from the next accountability moment. The Code Refresh spring 2026 vote creates a natural policy cluster to anchor action.

---

## 6. Demographic Predictors

| Factor | City figure | Political implication |
|---|---|---|
| Renter proportion | ~56.5% | Well above the 45% threshold that signals a large latent LVT constituency; renters are economic beneficiaries as land costs fall. However, renter political translation requires organized turnout — Richmond Tenants Union's nascent status is a gap. |
| Median age | 34.7 | Young city. Prior CLE/PPI polling shows under-40 voters favor LVT more strongly. Favorable base but requires turnout infrastructure. |
| % under 35 | ~38% (est. from ACS) | Large cohort; VCU and UR student populations add further young-adult concentration. Lynch's District 5 (VCU corridor) is particularly relevant. |
| Partisan lean | Harris +66pp (82% vs 16%, 2024) | One-party Democratic environment. The relevant coalition dynamic is intra-Democratic: progressive housing advocates vs. more cautious fiscal Democrats. LVT's anti-speculation and housing-equity arguments fit the progressive wing; revenue-neutrality addresses fiscal-moderate concerns. No Republican opposition to worry about. |
| Homeownership rate | 43.5% | Lower than national average; high homeownership in Districts 4, 8, 9 but low in central/northern districts. Must use district-specific data rather than city-wide averages when talking to council members. |
| Median household income | $64,587 | Below Virginia ($88K) and US ($75K) medians. Low-income context means commercial tax increase concerns ("business flight") are real; but it also means affordable housing salience is very high. |

Sources: [U.S. Census Bureau QuickFacts — Richmond city](https://www.census.gov/quickfacts/richmondcityvirginia); [ACS 5-year estimates via Data USA](https://datausa.io/profile/geo/richmond-va/); [Axios Richmond 2024 election results](https://www.axios.com/local/richmond/2024/11/08/richmond-area-2024-election-results-voters)

---

## 7. Coalition Map

|  | For LVT | Against LVT |
|---|---|---|
| **Organized** | **RVA YIMBY** (demonstrated capacity, parking/ADU wins; not yet engaged on LVT). **Better Housing Coalition** (potential ally if MWCLT impact is addressed; has council relationships). **University of Richmond PILR** (academic backing; 2022 analysis supports LVT for affordable housing). | **Virginia Realtors** (opposed rent stabilization in Richmond; likely to oppose commercial property tax increases). **Virginia Apartment Management Association** (same track record). **Greater Richmond Chamber of Commerce** (no specific position found, but 78% commercial tax increase gives them standing to oppose). |
| **Latent / unorganized** | ~130,000 Richmond renters (economic beneficiaries over time; low current organization). Young voters and VCU/UR student populations. SFR homeowners in Districts 4, 8, 9 (model shows clear majority benefit). Small developers and builders (lower improvement millage benefits development economics). | SFR homeowners in Districts 1, 2, 5 (majority see increases under model; need targeted constituent outreach or different framing). Small commercial landlords (face increases; less organized than Realtors). Maggie Walker CLT (72 parcels; CLT as land-owner faces higher land tax — needs a policy conversation or exemption). |

**Organization notes:**
- **RVA YIMBY**: Won two unanimous council votes in 2024 (parking minimums, ADUs). Has demonstrated the capacity to move the full council on pro-housing measures. If briefed on the LVT/Code Refresh connection, they are the most credible organizational advocate.
- **Virginia Realtors**: Statewide organization with a Richmond lobbyist presence. Opposed rent stabilization. Would need to be engaged early if commercial property concerns can be partially addressed (e.g., phased implementation).
- **Maggie Walker CLT**: 72 CLT parcels are in the parcel data. As land-owner, the trust would face higher land taxes under LVT. This is a values conflict that should be addressed proactively — not ignored — by carving out a policy conversation with MWCLT leadership before the ordinance is introduced.

---

## 8. Official Alignment Score

- Votes required: 5 of 9 council members (simple majority)
- Officials researched: 9 council members + Mayor (mayor does not vote on ordinances)
- Score breakdown: Breton (0), Jordan (-1), Gibson (0), Abubaker (+1), Lynch (+1), Robertson (0), Newbille (0), Trammell (+1), Jones (0)
- Sum: +2 / 9 members = mean +0.22 → **Split / uncertain**
- Note: confidence is mostly Low for scored 0 members; true range is wide

**Key swing votes:**
1. **Nicole Jones (D9)** — her district shows 84.4% SFR wins and -9.2% median change. The homeowner-relief argument is overwhelming in her district. She is a first-term member with no established position; presenting the district-specific data is the highest-ROI single conversation.
2. **Cynthia Newbille (D7, Council President)** — 47.1% SFR wins (near break-even), severe housing/eviction crisis in the East End, and council presidency gives her agenda-setting power. She is both the most important swing vote and the most credible coalition-builder if she comes on board. The anti-speculation/vacant-land frame is the right entry point for her district.

**Path to 5:** Abubaker (D4) + Lynch (D5) + Trammell (D8) = 3 confirmed lean-yes. Jones (D9) = strong persuasion target. Newbille (D7) = coalition leader if engaged early. That is the minimum winning coalition: 3 + 2.

**Council President role:** In Richmond, the Council President sets the agenda for public hearings and committee assignments. Newbille's support is thus doubly valuable — both as a vote and as the procedural gate. If she opposes or is neutral, she can delay introduction indefinitely.

---

## 9. Structural Viability Score

| Factor | Score (0–2) | Rationale |
|---|---|---|
| Electoral math | 1 | 51.2% of SFR parcels see a decrease — in the 40–60% range. The district analysis shows only 3 of 9 districts have SFR majority wins, meaning the homeowner framing carries 3 votes, not 5. Score capped at 1, not 2. |
| Renter proportion | 2 | 56.5% renter rate is well above the 45% threshold. Richmond's renter base is one of the largest structural LVT constituencies in Virginia. |
| Housing crisis salience | 2 | #2 eviction rate nationally, dominant campaign and council issue, $25M+ mayoral housing investment. Housing affordability is at peak salience. |
| Legal pathway ease | 2 | Tier 1 — city council ordinance under existing state authority. No new legislation, no referendum, no state action required. Easiest possible pathway. |
| Organized ally strength | 1 | RVA YIMBY is active with recent wins but has not yet engaged on LVT specifically. One demonstrated-capacity organization, not yet focused on LVT. If RVA YIMBY formally adopts LVT as a priority, this rises to 2. |
| **Total** | **8/10** | Strong structural foundation. The gap is political, not structural. |

---

## 10. Strategic Framing

**Recommended primary frame: Blight / Vacant Land + Housing Production**

The model data (7.3% vacant parcels, median +119% tax change on vacant land) and the political environment (Code Refresh, dominant housing crisis) together create the strongest available frame. Lead with the problem: Richmond has thousands of vacant lots sitting empty while families cannot find affordable housing. LVT makes land-banking expensive and development cheap — it's the tax reform that finally turns the code refresh into economic reality. This frame:
- Works in every district regardless of SFR win/loss status
- Is politically coherent with the Code Refresh vote
- Does not require the problematic income-quintile equity argument
- Has prior endorsement in Richmond public discourse (Virginia Mercury 2023, UR Law Review 2022)

**Recommended secondary frame: Homeowner Tax Relief (district-specific)**

For outreach to Abubaker (D4), Trammell (D8), and Jones (D9) specifically: "84% of homeowners in your district would pay less." This is a direct constituent service argument that complements the broader blight frame and gives each member a district-specific talking point. Do NOT lead with this frame city-wide — it fails in 6 of 9 districts.

**Frames to avoid:**
- "Income-progressive tax reform" — the income quintile data (lower-income block groups show higher mean changes) can be used against this frame. The mean is driven by vacant/commercial parcels, not SFR owners, but the rebuttal is complex. Don't open this door.
- "Revenue boost" — LVT is revenue-neutral in this model. Claiming a revenue increase misrepresents the model and will be fact-checked.
- "All homeowners benefit" — demonstrably false for 6 of 9 districts. Any council member can find this data, and using a false claim destroys credibility with the rest of the argument.

**Frames to address proactively (before opponents raise them):**
- "This hurts lower-income neighborhoods" → Counter: vacant lot owners face higher taxes; homeowners in those neighborhoods benefit (show district-specific SFR median). The burden falls on speculators, not residents.
- "This hurts small businesses" → Counter: improvement-intensive businesses (those who have actually built something) pay less. Only land-heavy uses (surface parking, vacant lots) pay more.
- "The CLT will be penalized" → Counter: acknowledge the MWCLT concern directly, open a policy conversation with MWCLT leadership, and (if needed) propose an exemption for CLT-held land (which would require Tier 4 state enabling but could be addressed in a subsequent amendment).

### Key Talking Points (Grounded in Model Data)

1. **"84% of Southwest homeowners and 84% of Southside homeowners pay less."** (Districts 4 and 9 have 78% and 84% SFR winner rates. For Abubaker and Jones, this is the core constituent message.)
2. **"5,275 vacant lots — 7.3% of the tax base — would face a median tax increase of 119%. That makes sitting on an empty lot while your neighbors need housing very expensive."** (Blight frame, supported directly by model data.)
3. **"Revenue-neutral. The city collects the same $526 million. The bill just shifts toward land and away from the buildings people live and work in."** (Addresses Mayor Avula's revenue concern and fiscally-cautious members.)
4. **"Richmond already has the legal authority. No state bill needed. The General Assembly gave Richmond this power in 2020. We can act by ordinance."** (Addresses the practical objection that it requires new legislation.)

---

## 11. Open Questions and Research Gaps

1. **Lynch's LVT statement source:** The Richmond Together 2024 questionnaire page was inaccessible. Lynch's LVT statement was found in a web search snippet — the original questionnaire text should be confirmed before quoting Lynch directly.
2. **Top vacant land owners:** The model export does not include owner names for vacant parcels. Identifying the top 10–20 largest vacant land holders (by acreage or assessed land value) is the single most impactful additional research step. Institutional or corporate land-bankers make vivid political targets; scattered small individual lots do not.
3. **Robertson's (D6) position:** No public statement found on property taxes or housing beyond one procedural vote. Searching D6 constituent newsletters, council statements, and 2024 campaign materials would fill this gap.
4. **Breton's (D1) position:** Same gap. West End voters would face the most unfavorable model outcomes of any district (32.5% SFR wins), making Breton the most likely no-vote; confirming this before introducing the ordinance allows the coalition to plan accordingly.
5. **Commercial real estate opposition magnitude:** Virginia Realtors and VAMA track records on rent stabilization are established; their actual position on split-rate taxation (which they have not publicly addressed) should be researched before the ordinance is introduced. A pre-introduction briefing of key commercial stakeholders may reduce surprise opposition.
6. **MWCLT impact and carve-out:** 72 CLT parcels would see higher land taxes. MWCLT leadership should be briefed before ordinance introduction. If a CLT exemption is desired, research the Va. Code authority for it (§58.1-3221.1 prohibits altering valuations but does not address exemption-from-rate for specific ownership types — this may require Tier 4–5 enabling).
7. **Demographics:** The ACS data used is 2022–2023. The 2024 5-year estimates should be confirmed when released.

---

## 12. Sources

**Section 2 — Legal brief and model**
- [Analysis: Richmond Legal Brief](../legal/richmond.md)
- [Richmond GeoHub — Council Districts FeatureServer](https://services1.arcgis.com/k3vhq11XkBNeeOfM/arcgis/rest/services/CouncilDistricts/FeatureServer)

**Section 3 — Political actors**
- [RVAHub — New 2025-2028 Richmond City Council Members (Jan 3, 2025)](https://rvahub.com/2025/01/03/new-2025-2028-richmond-city-council-members-administered-oaths-of-office/)
- [rva.gov — Council Contacts](https://www.rva.gov/richmond-city-council/council-contacts)
- [The Richmonder — Siding with Avula, Council Rejects Push to Lower Real Estate Tax Bills](https://www.richmonder.org/siding-with-avula-council-rejects-push-to-lower-real-estate-tax-bills/)
- [VPM — Richmond Council Votes to Hold Real Estate Tax Rate Steady (Nov 2024)](https://www.vpm.org/news/2024-11-12/richmond-council-votes-real-estate-tax-rate-nye-trammel)
- [VPM — Richmond City Council Votes Down Real Estate Tax Relief Proposal (Oct 2025)](https://www.vpm.org/news/2025-10-15/rva-council-real-estate-tax-trammell-avula-newbille-donald)
- [The Richmonder — As Home Values Rise Again, Trammell Proposes Lowering Richmond's Property Tax Rate](https://www.richmonder.org/as-home-values-rise-again-trammell-proposes-lowering-richmonds-property-tax-rate/)
- [The Richmonder — Now's Not the Time to Cut Richmond's Property Taxes, Avula Says](https://www.richmonder.org/nows-not-the-time-to-cut-richmonds-property-taxes-avula-says/)
- [Kenya Gibson — Considerations for the Code Refresh (Medium)](https://kenya-gibson.medium.com/considerations-for-the-code-refresh-zoning-the-richmond-we-want-to-build-da2940f39d4d)
- [Richmond Together — Stephanie Lynch 5th District Questionnaire](https://www.richmondtogether.org/p/stephanie-lynch-5th-district-city.html)

**Section 5 — Political environment**
- [Virginia Mercury — Land Value Taxes Could Cut Homeowners' Costs (May 2023)](https://virginiamercury.com/2023/05/03/land-value-taxes-could-cut-homeowners-costs-why-havent-virginia-localities-enacted-them/)
- [Richmond PILR — How Land Value Taxes Could Change Quality Affordable Housing in Richmond (2022)](https://pilr.richmond.edu/2022/10/06/how-land-value-taxes-could-change-quality-affordable-housing-in-richmond/)
- [VPM — Richmond City Council Declares Public Crisis for Evictions (Sep 2024)](https://www.vpm.org/news/2024-09-24/richmond-city-council-evictions-affordable-housing-stephanie-lynch)
- [VPM — Richmond's Code Refresh Aims to Rewrite Rules (Sep 2025)](https://www.vpm.org/news/2025-09-18/richmond-zoning-code-refresh-update-housing-development-vonck-robertson)
- [RVA YIMBY on Action Network](https://actionnetwork.org/groups/rva-yimby)
- [Richmond Tenants Union](https://richmondtenantsunion.org/)
- [Progress and Poverty Institute — Virginia Takes Four More Steps Towards LVT](https://progressandpovertyinstitute.org/virginia-takes-four-more-steps-towards-lvt/)

**Section 6 — Demographics**
- [U.S. Census Bureau QuickFacts — Richmond city, Virginia](https://www.census.gov/quickfacts/richmondcityvirginia)
- [Data USA — Richmond, VA](https://datausa.io/profile/geo/richmond-va/)
- [Axios Richmond — 2024 Election Results](https://www.axios.com/local/richmond/2024/11/08/richmond-area-2024-election-results-voters)

**Section 7 — Coalition**
- [The Richmonder — Rent Stabilization Bills Backed by Richmond Fail in Virginia GA](https://www.richmonder.org/rent-stabilization-bills-backed-by-richmond-fail-in-virginia-general-assembly/)
- [Better Housing Coalition — Who We Are](https://www.betterhousingcoalition.org/who-we-are/)
