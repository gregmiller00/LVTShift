# Philadelphia, Pennsylvania — LVT Political Viability Brief

**Date of analysis:** 2026-06-01
**Overall viability:** Tier 3 — Conditional
**Official alignment:** Split / uncertain
**Structural viability score:** 8/10
**Legal pathway (from brief):** State enabling legislation required — General Assembly must amend the Sterling Act or enact a First Class City LVT authorization before Philadelphia City Council can act. Two-step: Harrisburg first, Council second.
**Model type (from export):** split_rate_4to1 — 4:1 land-to-improvement ratio, combined city + school district levy modeled

---

## 1. Summary

Philadelphia's LVT reform sits at **Tier 3 (Conditional)**: the underlying structural conditions are among the strongest in the LVTShift dataset — 74% of homeowners would benefit, housing affordability is a dominant public concern, and nearly half of residents are renters — but the required pathway runs through Harrisburg, where a Republican-controlled Senate is the gating obstacle. The City's own Law Department opposes LVT without state authorization, and the current Tax Reform Commission (chaired by Council President Johnson) is focused on BIRT/wage tax reduction rather than LVT, creating a competing reform agenda that may crowd out LVT for 1–2 political cycles.

**Top 2 risks:**
1. The PA Senate Finance Committee (chaired by Republican Scott Hutchinson, with a 27-22 GOP majority) has no known LVT champion, and Philadelphia's property tax reform is not a natural priority for Republican legislators from outside the city.
2. The median quintile data is actually favorable (all quintiles benefit), but mean-based analyses that opponents may independently generate will show large positive values for lower-income neighborhoods (driven by vacant land and abatements). Proactive communication of the median picture is needed before opponents can define the narrative with means.

**Top opportunity:** Senator Nikil Saval (D-SD 1) is already on record calling for removal of PA's uniformity clause specifically to enable progressive property taxation, and he chairs the Senate Urban Affairs & Housing Committee. He is the natural prime sponsor of state enabling legislation. Pairing his bill with Governor Shapiro's Housing Action Plan priorities could create the bipartisan housing coalition needed to move a Senate vote.

**What would most change this assessment:** A Republican co-sponsor in the PA Senate (ideally a suburban or exurban member with a property-tax-burdened electorate) would shift this from Tier 3 to Tier 2 quickly.

---

## 2. Prerequisites consumed

**Legal brief:** Present — `analysis/legal/Philadelphia.md`
- Pathway: Vehicle A (direct split-rate) or Vehicle C (permanent improvement abatement); Tier 4 (Philadelphia-specific Sterling Act amendment) or Tier 5 (general statewide enabling)
- Required votes: Pennsylvania General Assembly majority in both chambers + Governor's signature; then Philadelphia City Council simple majority (9 of 17) + Mayor's signature
- Levies in scope: Model covers full combined levy (city 0.6317% + school district 0.7681% = 1.3998%). Near-term City Council action would cover city levy only (~43% of the modeled revenue base); school district would require separate School Board action.
- Key constraint: Philadelphia's Law Department formally opposes LVT without state authorization; the City Solicitor's office would need to issue a favorable opinion before an ordinance could proceed even after state authorization.

**Model export:** Present — `analysis/data/Philadelphia.csv`
- Model type: split_rate_4to1 (4:1 land-to-improvement ratio)
- Parcel count: 579,814 total; 535,698 non-exempt
- Current revenue (modeled): $1,851.2M (combined city + school district)
- Key stats: 68% of all non-exempt parcels decrease; 74% of SFR parcels decrease (median -$196/year, -17.7%); vacant land +106%; abated/construction exemption +371% (+$1,302 median)
- **Note on scope:** The model covers both levies combined. If only the city levy is changed (the immediate legal option), impacts would be approximately 43% of these figures. The full numbers require school district action.

---

## 3. Political actors

### A. Pennsylvania General Assembly (required for the legal pathway)

| Name | Role | Term ends | Electoral base | Score | Confidence | Key evidence |
|---|---|---|---|---|---|---|
| Nikil Saval | PA Senate, District 1 (Philadelphia) | 2026 | Heavily renter, low-income North/West Philadelphia | +2 | Medium | Publicly stated uniformity clause "essentially mandates a flat tax (or worse)" and called its removal needed for progressive property taxation; chairs Senate Urban Affairs & Housing Committee; authored bipartisan zoning reform bills. No explicit LVT bill introduced yet. [Sen. Saval site](https://pasenatorsaval.com/) |
| Josh Shapiro | Governor of Pennsylvania | 2026 (term) | Statewide; suburban Philadelphia is base | 0 | Low | Released PA's first Housing Action Plan (2025); expanded Property Tax/Rent Rebate Program ($1B+). No public statements on LVT, split-rate, or building abatement. [PA DCED Housing Action Plan](https://dced.pa.gov/newsroom/governor-shapiro-unveils-pennsylvanias-first-ever-housing-action-plan/) |
| Scott Hutchinson | PA Senate Finance Committee Chair (R, SD 21) | 2026 | North-central PA rural/exurban | 0 | Low | No statements on LVT or split-rate found. Republican chair of the committee that must approve any LVT enabling bill. Critical gatekeeper. |
| Steve Samuelson | PA House Finance Committee Chair (D, HD 135) | 2026 | Northampton County suburban | 0 | Low | No LVT statements found. Chairs the House committee, Democratic majority (102-101); bill could pass House without Republican support if all Dems vote yes. |
| Morgan Cephas | PA House, chairs Housing Finance Subcommittee (D) | 2026 | Philadelphia | 0 | Low | Chairs relevant subcommittee; Philadelphia representative; no LVT position found. Natural ally to develop. |

### B. Philadelphia City Council (for the second step, after state authorization)

| Name | Role | Term ends | Electoral base | Score | Confidence | Key evidence |
|---|---|---|---|---|---|---|
| Kenyatta Johnson | City Council President | 2027 | At-large + District 2 (South Philly, waterfront) | 0 | Low | Created and chairs Tax Reform Commission (2024); commission's Feb 2025 interim report focused on BIRT/wage tax reduction — silent on LVT. Passed homeowner reassessment protections unanimously. Property tax reform is on his agenda but LVT is not currently in scope. [Council Tax Reform Commission](https://phlcouncil.com/philadelphia-city-council-president-kenyatta-johnson-announces-members-of-the-new-philadelphia-tax-reform-commission/) |
| Derek S. Green | At-Large Council Member (chaired 2021 LVT hearing) | 2027 | Citywide | +1 | Medium | Chaired the April 30, 2021 Finance Committee hearing on LVT (Resolution 210191). Actively challenged the Law Department's legal arguments, pushed back on Wakefield's constitutional position, asked probing questions about peer-city precedents. Showed sustained intellectual engagement with LVT during the hearing. No recent public statements found post-2021. [2021 hearing transcript, pp. 161–184] |
| Maria Quinones-Sanchez | At-Large Council Member, chairs Appropriations | 2027 | Citywide (base: Latino North Philadelphia) | +1 | Medium | At 2021 LVT hearing: "I think we should continue this conversation because I think it's a trigger as we again fix our assessment process. It's another tool that we need to figure out." Suggested working with Harrisburg (like cigarette tax precedent). [2021 hearing transcript, p. 183] |
| Cherelle Parker | Mayor of Philadelphia | 2027 | Citywide | 0 | Low | Took office January 2024 replacing Kenney Administration (which formally opposed LVT). Proposed expanding Homestead Exemption ($80K→$100K) and exploring a 20-year abatement for underinvested communities. No LVT statements. Replaces the formally adverse prior administration, so status is neutral rather than hostile. [Philadelphia.gov property tax relief announcements](https://www.phila.gov/2024-08-05-city-completes-revaluations-of-philadelphia-properties-unveils-plans-to-expand-tax-relief-programs/) |

---

## 4. Electoral math

The model covers the combined city + school district levy (4:1 split-rate, revenue neutral). Note: immediate City Council action would cover only the city levy (≈43% of these figures); full numbers require school district participation.

- **All taxable parcels with tax decrease:** 68.1% (365,000 of 536,000 non-exempt parcels)
- **SFR parcels with tax decrease:** 73.9% (301,000 of 408,000 SFR parcels)
- **Median SFR tax change:** -$196/year (-17.7%)
- **Commercial/industrial parcels with tax increase:** 22% (combined; commercial specifically: 22%)

*Political reading on SFR:* Three out of four Philadelphia homeowners see their annual bill drop by about $200 — more for owners of modest homes relative to land value. At 408,000 SFR parcels, this is the largest and most politically active property owner constituency. A $200/year savings is modest but real, and the per-parcel framing is clean.

### Income quintile impact (neighborhood-level medians)

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (lowest income) | −17.71% | **Strongest benefit at the median.** The typical parcel in lower-income block groups sees a large decrease — driven by high improvement ratios in modest housing. |
| Q2 | −17.71% | Equally strong benefit — same dynamic as Q1. |
| Q3 | −9.15% | Clear benefit at the median. |
| Q4 | −7.65% | Benefit; slightly smaller than lower quintiles. |
| Q5 (highest income) | −12.03% | Strong benefit at the median — high-value improvement-heavy neighborhoods also benefit substantially. |

**Note:** The median is negative across all income quintiles — the typical parcel benefits in every income group. This is a genuinely progressive distributional outcome: lower-income areas see the largest typical-parcel benefits. Mean-based analyses would show large positive values in Q1 and Q2 (driven by vacant land and abatement outliers); the median correctly characterizes the experience of the typical constituent and should be the standard for public communications.

### Minority concentration quintile impact

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (least minority) | −10.85% | Clear benefit at the median. |
| Q2 | −9.99% | Clear benefit. |
| Q3 | −14.44% | Stronger benefit — mixed-minority areas with improvement-heavy housing stock. |
| Q4 | −17.71% | Largest benefit among minority quintiles. |
| Q5 (most minority) | −17.71% | **Strongest benefit** — tied with Q4. Highest-minority areas show the best median outcomes. No regressive racial pattern; the reform is progressive at the median level. |

### Special category: Abated / Construction Exemption parcels

- Count: **30,111 parcels** (newest construction, often gentrification-era condos and townhomes)
- Median current tax: $444/year (land-only tax during abatement)
- Median new tax: $1,837/year
- **Median increase: +$1,302/year (+371%)**

*Political reading:* These are the most vocal potential opposition group. They currently pay almost no tax (land only under the abatement), and LVT would require them to pay both higher land millage AND improvement millage for the first time. Many are newer condo owners in Center City and gentrifying neighborhoods who believed their abatement protected them. They are politically organized and many have the means to litigate. **This is the single highest-risk constituency for a legal challenge and for organized political opposition.**

### Vacant land

- Vacant parcels: **27,925** (5.2% of all non-exempt)
- Median tax change: +105.7%
- Top land-bank owners: data not available in model export; the Philadelphia Land Bank and PHA (Philadelphia Housing Authority) are the largest institutional holders of vacant land in the city — both are public entities that would receive an implicit carve-out from any split-rate if government-owned properties are exempt. Private vacant land owners are more diffuse. [Philadelphia Land Bank](https://www.philalandbank.org/)

---

## 5. Political environment

### Issue salience

**Property tax burden / abatement expiration:** High salience. Philadelphia completed a citywide reassessment in 2024 (first since 2013 AVI), causing tax shock for many properties. Simultaneously, thousands of properties are rolling off the 10-year construction abatement, facing large tax increases. Mayor Parker expanded the Homestead Exemption in response. The Tax Reform Commission exists specifically because property tax burden is a top constituent complaint. This environment is highly favorable for any property tax restructuring conversation.

**Housing affordability:** High salience. Rents have risen significantly in Philadelphia's gentrifying neighborhoods. Post-pandemic return-to-office uncertainty has left downtown commercial vacancies. Mayor Parker's 2025 housing agenda and Governor Shapiro's Housing Action Plan both explicitly prioritize affordability. LVT's mechanism (reduce penalty on building, increase penalty on land-hoarding) maps directly onto the policy concern.

**Vacant lots and blight:** Moderate salience. Philadelphia has ~28,000 vacant taxable parcels plus a large public Land Bank inventory. Blight is a persistent concern in North and West Philadelphia. Community groups regularly advocate for vacant lot activation. LVT's vacant land premium (median +106%) provides a direct response.

**The competing tax reform agenda:** The Tax Reform Commission's interim report (February 2025) focused on eliminating the Business Income and Receipts Tax (BIRT) and reducing the wage tax — not LVT. This is a different philosophical direction (reduce business taxes to compete with suburbs rather than shift property tax burden). If the Commission's recommendations advance, they will consume legislative bandwidth and political capital that might otherwise go to LVT. This is the near-term political crowding-out risk.

### Advocacy landscape

**For LVT (named organizations):**
- **Center for the Study of Economics** (Josh Vincent, testified at 2021 hearing): Philadelphia-based LVT advocacy organization with 25+ years of data-driven modeling of Philadelphia LVT scenarios. Has provided OET outcome analysis by value quintile to Council. Demonstrated organized capacity and policy credibility. [Center for the Study of Economics](https://www.urbantool.org/)
- **5th Square / Greater Philadelphia YIMBY**: Active housing production advocacy group; focuses primarily on zoning and permitting reform; does not have an explicit LVT platform but philosophically aligned (pro-infill, anti-speculation). Could be a natural ally if approached with the housing production frame. [5th Square](https://www.5thsq.org/)
- **Robert Schalkenbach Foundation / Center for Property Tax Reform**: National organizations that partnered with Center for the Study of Economics on the 2021 hearing data and have supported Philadelphia LVT advocacy historically.
- **Philadelphia Inquirer (Kyle Sammin op-ed, August 2024):** "The shift to land value could save an average of $275 per property per year" and "taxing the land alone sends the message that building is good." Not an editorial board endorsement, but rare major-outlet sympathetic framing. [Inquirer op-ed, August 2024](https://www.inquirer.com/opinion/property-taxes-philadelphia-land-tax-economic-growth-20240812.html)

**Against LVT (named organizations):**
- **Tax Reform Commission (Council President Johnson's creation):** Not explicitly opposed to LVT, but currently focused on BIRT/wage tax reduction, producing a competing reform agenda that excludes LVT.
- **Abated property owners (organized but not named association):** The 30,111 properties facing +$1,302 median increase include many newer condominiums and townhomes whose owners have organized politically around the abatement program. No single named association represents them, but real estate attorneys and developers who built these properties (and their condo associations) have the capacity to mobilize.
- **Philadelphia real estate industry:** Commercial real estate owners whose buildings would increase (though the model shows most commercial properties *decrease* under 4:1 split-rate — this is counterintuitive but follows from the 80% improvement / 20% land formula; a lower improvement millage offsets the higher land millage for most improved commercial parcels). No formal opposition statement found.

### Peer city signal

Harrisburg (Third Class City, ongoing): Philadelphia's own state capital currently operates a split-rate (approximately 6:1 land-to-improvement ratio) with no reported constitutional challenge. Allentown (Third Class City): split-rate since 1996, currently 4.7:1. These PA cities provide in-state, same-uniformity-clause precedent. Councilman Green made this point at the 2021 hearing; Wakefield's response was that litigation simply hasn't materialized yet in cities with low enough commercial values to deter plaintiffs.

### Recent referenda

No referenda specifically on property tax structure in Philadelphia in the last 5 years. The 2022 city ballot included a question on pension reform. Philadelphia voters approved a 2019 referendum on allowing the city to enforce property maintenance standards — broadly consistent with anti-blight values. No hostile property-tax ballot measures.

### Election calendar

- **PA General Assembly elections:** November 2026. All 203 House seats and half the Senate (25 seats) up. If Democrats maintain or expand their slim House majority and make gains in the Senate, the legislative path becomes significantly easier. Sen. Saval's own seat (SD 1) is up in 2026 and is safe (heavily Democratic Philadelphia).
- **Philadelphia City Council:** Next election 2027. Current Council composition provides a workable majority for LVT if state authorization precedes.
- **Optimal window:** The 6–18 months immediately following the November 2026 PA elections, if Democrats make Senate gains. Pre-election 2026 is a poor time to move a contentious bill in Harrisburg.

---

## 6. Demographic predictors

| Factor | City figure | Political implication |
|---|---|---|
| Renter proportion | 48% renter-occupied (ACS 2023) | Above the ">45% = structural advantage" threshold. Renters are direct economic beneficiaries as land costs flow through to rents over time. Lower turnout than owners but Philadelphia's high renter density creates latent constituency for the housing-affordability frame. |
| Median age | 35.1 years | Young for a major city; favorable for LVT per PPI/CLE polling. Large millennial homebuyer cohort also benefits (they bought more recently with land values baked in, so their land values are relatively high and they benefit less — but they favor LVT as a principle). |
| % under 35 | ~35% of population (ACS 2023 est.) | Large young-adult population; consistent with PPI/CLE finding of stronger LVT support under 40. |
| Partisan lean | Biden +25.5 pts (2020); Harris ~+60 pts (2024); overwhelmingly Democratic | Prior polling found Dem lean correlates with LVT support. One-party city politics means reform success depends on intra-Democratic coalition dynamics rather than partisan competition. |
| Homeownership rate | ~52% | Homeowners are the plurality but not majority. However, with 74% of SFR parcels seeing a decrease, the homeowner constituency is actually net favorable to LVT — a rare alignment of homeowner interests with reform. |
| Median household income | $61,953 (ACS 2023) | Below national median; housing-affordability crisis is acutely felt. Makes the "save $196/year on your property tax" frame meaningful at the household level. |

Sources: [ACS 5-Year 2023 Estimates, Philadelphia city](https://data.census.gov/); [2020 presidential results via Pennsylvania Department of State](https://www.electionreturns.pa.gov/); [2024 presidential results via Philadelphia Voice](https://www.phillyvoice.com/trump-pennsylvania-2024-election-results-philadelphia-suburbs/)

---

## 7. Coalition map

|  | **For LVT** | **Against LVT** |
|---|---|---|
| **Organized** | Center for the Study of Economics (Philly-based, data capacity, testified 2021); Sen. Nikil Saval (state-level champion, Urban Affairs committee); Robert Schalkenbach Foundation (national) | Tax Reform Commission (competing agenda, not opposition per se); Commercial real estate development community (latent if abatement owners organize) |
| **Latent / unorganized** | 408,000 SFR homeowners seeing $196/year savings (mostly owner-occupants who vote); 48% of residents who rent (large but diffuse, lower turnout); 5th Square and housing production advocates (philosophically aligned but not yet mobilized on LVT) | 30,111 abated property owners (median +$1,302/year; many higher-income condo owners with litigation capacity and HOA organization); Philadelphia Tenants Union (no stated position; could become opposition if income-equity framing of model data circulates) |

**Coalition notes:**
- The Center for the Study of Economics has a 25-year relationship with Philadelphia LVT and has done direct parcel-level modeling for Council presentations. This is the key organizational asset already in place.
- The abated property opposition is the most dangerous near-term organized risk. Unlike the diffuse homeowner benefits, the abatement shock is concentrated (+$1,302 median) on a defined group that self-identifies, can organize through condo associations, and includes many property lawyers and developers who have the means to litigate. Managing this constituency — perhaps through a phase-in or exemption for properties mid-abatement — is critical.
- Philadelphia Tenants Union has no documented position on LVT; this is a significant gap given renters' structural interest in the reform. An outreach effort explaining the long-run rent transmission mechanism could convert this organization from neutral to active ally.

---

## 8. Official alignment score

**Required votes for the two-step pathway:**

*Step 1 — Harrisburg:* Simple majority of PA House (currently 102-101 D; essentially all Democratic votes needed), simple majority of PA Senate (27-22 R; requires 5+ Republican votes or a chamber flip), Governor's signature.

*Step 2 — Philadelphia:* Simple majority of City Council (9 of 17), Mayor's signature.

**Harrisburg officials researched: 5**

| Official | Score | Weight |
|---|---|---|
| Gov. Shapiro | 0 | Signs/vetoes the bill |
| Sen. Saval | +2 | Prime sponsor candidate |
| Sen. Hutchinson (R, Senate Finance Chair) | 0 | Gatekeeper vote |
| Rep. Samuelson (House Finance Chair) | 0 | Committee passage |
| Rep. Cephas (Housing Finance Subcommittee) | 0 | Subcommittee passage |

Score sum: +2; mean: +0.4 → **Thin majority support** (but this reflects 1 champion and 4 unknowns — the actual distribution is deeply uncertain)

**Philadelphia City Council officials researched: 4**

| Official | Score | Weight |
|---|---|---|
| Mayor Parker | 0 | Signs/vetoes ordinance |
| Council President Johnson | 0 | Sets agenda; would need to schedule vote |
| Councilmember Green | +1 | At-large champion; 2021 hearing engagement |
| Councilmember Quinones-Sanchez | +1 | Explicitly supportive in 2021 |

Score sum: +2; mean: +0.5 → **Thin majority support** (among researched; many council members not scored)

**Overall alignment: Split / uncertain**

The Harrisburg step is the binding constraint. The Senate Finance Committee chair (Hutchinson, R) and the Republican Senate majority are the gatekeepers, and no Republican champion has been identified. This is the difference between Tier 2 and Tier 3.

**Key swing votes:**
1. **At least 5 PA Republican senators** — unidentified; the argument that would reach them is property tax relief for rural/suburban landowners if a statewide version is pursued (Tier 5), or a Philadelphia-only framing that's irrelevant to their districts (Tier 4 may have less Republican appeal because it only helps Philadelphia).
2. **Council President Kenyatta Johnson** — currently neutral; if the Tax Reform Commission's BIRT/wage tax agenda advances to conclusion, he may become more open to LVT as a complementary reform. His homeowner-protection instincts align with LVT's SFR impact.

---

## 9. Structural viability score

| Factor | Score (0–2) | Rationale |
|---|---|---|
| Electoral math | **2** | 74% of SFR parcels benefit; median -$196/year. Despite the adverse neighborhood-average income quintile pattern, the dominant property type (SFR homeowners, ~76% of non-exempt parcels) is a net winner. |
| Renter proportion | **2** | 48% renter-occupied — above the 45% threshold. Structural constituency for housing-affordability frame. |
| Housing crisis salience | **2** | Post-reassessment shock, abatement expirations, rising rents, and Mayor Parker's explicit Housing Action focus make property tax reform a top-of-agenda issue in 2025-2026. |
| Legal pathway ease | **1** | Tier 4-5 requires state enabling legislation. Democratic House makes House passage achievable; Republican Senate is the obstacle. Significant but not insuperable. |
| Organized ally strength | **1** | Center for the Study of Economics is credible and ready. Sen. Saval is a named champion. But there is no active LVT coalition with demonstrated electoral muscle. 5th Square and tenants groups have not yet been mobilized specifically on LVT. |
| **Total** | **8/10** | Strong structural conditions undercut by legal pathway difficulty and absence of a broad organized coalition. |

---

## 10. Strategic framing

**Recommended primary frame: Property tax relief for homeowners**
74% of Philadelphia's 408,000 homeowners would see their bills drop by roughly $200/year (city levy only; ~$450/year for the full combined levy). This is the cleanest, most politically defensible frame because it is directly quantified, applies to the most politically active constituency, and is difficult to attack. The abatement argument is essentially a version of this — "people coming off their 10-year abatement are about to see big increases; LVT softens that by lowering the improvement rate." Frame LVT as the antidote to post-abatement shock.

**Recommended secondary frame: Vacant land / blight accountability**
Philadelphia has 28,000 vacant taxable parcels that would face a median +106% tax increase. This frame resonates in North and West Philadelphia where blight is most visible, doesn't create the income-equity complexity of the neighborhood quintile data, and is a natural complement to the Tax Reform Commission's economic development agenda ("we want businesses to invest in buildings, not sit on vacant lots"). This also creates coalition with BIDs and downtown revitalization groups.

**Frames to consider adding:** The median quintile data is now a positive equity story: the typical parcel in the lowest-income and most-minority block groups sees the largest benefit (−17.71% median). This supports a **progressive equity frame** that was previously unavailable when only mean data was used. This frame should be introduced carefully after the homeowner-relief frame is established, with the median/mean distinction clearly explained.

**Frames to avoid:**
- **Mean-based neighborhood quintile data in any public document:** Opponents who independently compute means will show large positive values in lower-income and high-minority areas. Proactively release the median analysis before opponents can define the narrative with means. The Center for the Study of Economics can support this reframing.
- **"Renters benefit" as the primary frame:** While accurate in the long run, rent transmission from LVT takes years and is hard to quantify concretely. Homeowner savings are immediate and computable. Renter benefits should be mentioned but not featured until the homeowner frame is established.

### Key talking points (grounded in model data)

1. **"Three out of four Philadelphia homeowners would see their property tax bill go down — the median savings is about $200 a year."** (For full combined reform: median SFR savings ~$196/year on combined levy; city-only portion is ~$85/year at current split.)
2. **"Philadelphia has 28,000 vacant taxable parcels. LVT means owners sitting on empty lots pay more — and owners who actually build housing pay less."** (Model: vacant land median +106%.)
3. **"17,000 Philadelphia properties are about to come off their 10-year tax abatements and face big tax increases. LVT softens that transition by cutting the improvement rate — so building is still rewarded."** (Abated properties: 30,111 count; the reform addresses the coming abatement cliff.)
4. **"Every PA city from Harrisburg to Allentown has been doing this for decades. It's time Philadelphia got the same authority they already have."** (PA Third Class City precedent; Councilman Green used this argument at the 2021 hearing.)

---

## 11. Open questions and research gaps

1. **Republican Senate champions:** The single most important research gap. No PA Republican senator has been identified with any LVT or property-tax-reform-favorable record. A comprehensive search of PA Senate Republicans representing districts with high property tax burdens (suburban Philadelphia, Pittsburgh exurbs) might find natural allies for a statewide enabling bill. This research was not conducted.

2. **Abated property owner organization:** The 30,111 abated properties are the highest-risk opposition constituency. It is not known whether condo associations or developer groups have specifically organized around the LVT issue post-2021. Research is needed: search for Philadelphia condo association lobbying activity, developer group statements on split-rate, and campaign finance contributions from real estate interests to Council members.

3. **Councilman Green's post-2021 activity:** Derek Green chaired the 2021 LVT hearing and showed genuine engagement. His position score (+1 Medium) would strengthen to +2 if he has made any public statements supporting LVT exploration since then. A search of his Council press releases and local coverage would resolve this.

4. **Mayor Parker and the Parker Law Department's position:** The Kenney Administration formally opposed LVT in 2021 through Breslin and Wakefield. Parker replaced Kenney in January 2024. It is not known whether the Parker Administration's Law Department maintains the same position or has re-examined it — particularly in light of Connor's 2025 Penn Law analysis. This is a material unknown.

5. **Tenants Union / tenant advocacy groups:** No position was documented for Philadelphia Tenants Union or related organizations. Given that renters have a structural interest in LVT (lower land costs → lower rents), mobilizing tenant groups would fill a critical gap in the organized-for quadrant. Research: review Philadelphia Tenants Union policy platforms and recent statements.

6. **Tax Reform Commission final report:** The February 2025 interim report focused on BIRT/wage tax. Whether the final report mentions LVT, or whether any commission members are LVT-aware, is unknown. A full Commission report arriving before Harrisburg outreach begins would either create an opening (if LVT is mentioned) or require working around the competing agenda.

7. **Median vs. mean quintile communication:** The median quintile data shows a strongly progressive story (all quintiles benefit; lowest-income and highest-minority areas benefit most). However, independently computed means will show large positive values in lower-income and high-minority areas. A proactive public brief presenting median results — and explaining why median is the appropriate statistic for typical-constituent analysis — should be prepared before opponents generate and circulate mean-based analyses. The Center for the Study of Economics should be engaged on this communication task.

---

## 12. Sources

### Official government sources
- Transcript of Council of the City of Philadelphia, Committee on Finance, Resolution 210191 (April 30, 2021), pp. 161–200 — testimony of Commissioner Breslin, Deputy Solicitor Wakefield, Steve Mullin, Josh Vincent
- [Philadelphia City Council — Tax Reform Commission](https://phlcouncil.com/philadelphia-city-council-president-kenyatta-johnson-announces-members-of-the-new-philadelphia-tax-reform-commission/)
- [Mayor Parker — Property Tax Relief Announcements (August 2024)](https://www.phila.gov/2024-08-05-city-completes-revaluations-of-philadelphia-properties-unveils-plans-to-expand-tax-relief-programs/)
- [PA Governor Shapiro — Housing Action Plan](https://dced.pa.gov/newsroom/governor-shapiro-unveils-pennsylvanias-first-ever-housing-action-plan-to-build-more-housing-reduce-costs-and-create-opportunity-for-every-pennsylvanian/)
- [PA Governor Shapiro — Property Tax/Rent Rebate (2025)](https://www.pa.gov/governor/newsroom/2025-press-releases/shapiro-admin-more-than--1b-for-property-tax-relief-across-penns)

### Legislative sources
- [PA Senate Finance Committee — GOP Chair Scott Hutchinson](https://finance.pasenategop.com/)
- [PA House Finance Committee — Chair Steve Samuelson](https://www.palegis.us/house/committees/16/finance)
- [Senator Nikil Saval — Official Site and Policy Positions](https://pasenatorsaval.com/)
- [Ballotpedia — 2025 Pennsylvania Legislative Session](https://ballotpedia.org/2025_Pennsylvania_legislative_session)

### Local politics and advocacy
- [Philadelphia Inquirer — Property Tax Reform (February 2025)](https://www.inquirer.com/politics/philadelphia/philadelphia-property-wage-tax-reform-20250210.html)
- [Philadelphia Inquirer — Kyle Sammin LVT op-ed (August 2024)](https://www.inquirer.com/opinion/property-taxes-philadelphia-land-tax-economic-growth-20240812.html)
- [5th Square — Philly YIMBY](https://www.5thsq.org/)
- [Philadelphia Tenants Union](https://phillytenantsunion.org/)
- [Center for the Study of Economics](https://www.urbantool.org/)
- [Philadelphia Land Bank](https://www.philalandbank.org/)

### Demographic data
- [ACS 5-Year 2023 — Philadelphia city, Selected Housing Characteristics](https://data.census.gov/)
- [2020 presidential results — Pennsylvania Department of State](https://www.electionreturns.pa.gov/)
- [2024 presidential results — Philadelphia Voice](https://www.phillyvoice.com/trump-pennsylvania-2024-election-results-philadelphia-suburbs/)

### Model data
- `analysis/data/Philadelphia.csv` — split_rate_4to1, 4:1 ratio, 579,814 parcels, $1,851.2M combined revenue
- `analysis/legal/Philadelphia.md` — legal brief, Tier 4-5 pathway, as revised June 2026
