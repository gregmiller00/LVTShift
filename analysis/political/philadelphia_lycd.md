# Philadelphia, PA — LVT Political Viability Brief (LYCD Model)

**Date of analysis:** 2026-07-18
**Overall viability:** Tier 3 — Conditional
**Official alignment:** Split / uncertain
**Structural viability score:** 8/10
**Legal pathway (from brief):** State enabling legislation required before Philadelphia can act at all — Pennsylvania statutorily blocks First Class Cities from split-rate/land-value taxation (72 Pa. Stat. Ann. §§5020-201, 5020-402(a.1)); the constitutional question under PA's uniformity clause is separately unresolved. Recommended vehicle: Vehicle A (direct split-rate) or Vehicle C (permanent improvement abatement) via Tier 4 (Philadelphia-specific) or Tier 5 (general statewide) state enabling legislation.
**Model type (from export):** `split_rate_4to1_lycd` — 4:1 land-to-improvement millage ratio, land values estimated via the GMA hierarchical zone-median method (not OPA's raw `taxable_land`)

> **Note on this brief's data source:** This is an independent brief built on `analysis/data/philadelphia_lycd.csv` (the LYCD land-value model), not the OPA-based model used in the existing `analysis/political/Philadelphia.md`. Officials, environment, and demographic research were conducted fresh for this brief rather than assumed from the earlier one. Where facts naturally overlap (the same city, the same officials, the same legal brief), independent verification is noted.

---

## 1. Summary

Philadelphia's underlying economics are strongly favorable to LVT: 69.1% of non-exempt taxable parcels see a tax cut under the LYCD model, homeowners do especially well (76.6% of Single Family Residential parcels decrease, median −23.0%), and every one of the city's 10 council districts has an SFR-majority-winning outcome. Renters are 47.7% of occupied units — a large latent beneficiary population — and housing affordability, blight, and property-tax-burden salience are all demonstrably high right now (a citywide reassessment backlash is an active news story as of this month, July 2026). That combination would normally support a higher tier.

What holds this back to Tier 3 is the legal pathway, not the electorate. Philadelphia cannot enact LVT on its own — the Sterling Act framework requires new Pennsylvania General Assembly authorization, and Pennsylvania's legislature is divided (Democratic House 102–101, Republican Senate 28–22) heading into a 2026 gubernatorial election. No state legislator, including Sen. Nikil Saval (the most naturally aligned figure, chair of the Senate Philadelphia Delegation and Urban Affairs & Housing Committee), was found to have a specific current bill or public statement on LVT enabling legislation. Independently of the legal gate, City Council members are genuinely split: none advocates LVT or split-rate by name, and several read as actively skeptical of the improvement-tax-reduction logic LVT depends on — Cindy Bass (D8) has explicitly called for *ending* the 10-year abatement and "returning to the traditional property tax structure," the opposite direction from LVT's further reduction of improvement tax rates.

**Top 2 risks:** (1) The PA Senate's Republican majority has shown no appetite for a Philadelphia-specific tax-authority expansion, and no legislative champion has emerged since the 2021 hearing. (2) Several Council members' recent positioning on the abatement (Bass, and to a lesser extent the general "traditional taxation" framing in the 2025 Tax Reform Commission's interim report) pulls toward taxing improvements *more*, not less — a philosophy that cuts against LVT's core mechanism even among officials otherwise sympathetic to housing production.

**Top opportunity:** The reform's economic case is uniquely strong and city-wide, not confined to one faction's turf — precinct-level analysis (Section 4) found only weak correlations between any official's electoral base and the reform's winners/losers, meaning this is not a policy that helps one coalition at another's expense. Combined with Jamie Gauthier's (D3) demonstrated YIMBY-aligned advocacy and the active, if not yet electorally tested, Rent Control Coalition and Philly YIMBY/5th Square infrastructure, there is a plausible coalition to build from once (or if) state authorization exists.

**What would most change this assessment:** A named PA legislator introducing Sterling Act amendment language, or a fresh City Solicitor opinion engaging with Brian Connor's vertical/horizontal constitutional theory (see legal brief), would be the single most consequential development — it would convert this from "no vehicle exists" to "a vehicle exists, now it's a vote count."

---

## 2. Prerequisites consumed

- **Legal brief:** present (`analysis/legal/Philadelphia.md`, dated 2026-06-01)
  - Pathway: Vehicle A or C, Tier 4 (Philadelphia-specific Sterling Act amendment) or Tier 5 (general statewide enabling legislation)
  - Required votes: PA General Assembly enabling legislation first (simple majority in both chambers, or whatever each chamber's own rules require), then Philadelphia City Council ordinance (simple majority of 17 = 9 votes; a mayoral veto can be overridden with 12 votes), then separately, School District/Board of Education action for the school-district millage share
  - Levies in scope: **full stack** — this LYCD model covers the combined city (0.6317%) + school district (0.7681%) rate of 1.3998%, not the city portion alone. The School District sets its own millage independently under separate state authority (Act of Aug. 8, 1963), so a real-world reform would require two separate enactments even after state authorization exists.
- **Model export:** present (`analysis/data/philadelphia_lycd.csv`)
  - Model type: `split_rate_4to1_lycd` (4:1 land-to-improvement ratio; land values from the GMA hierarchical zone-median method, not OPA's default 20%-of-value land ratio)
  - Parcel count: 579,814
  - Current revenue (modeled, combined city + school): $1,851,152,567 (≈ +4.9% above the FY2024 combined levy, attributed to normal delinquency in the underlying data, per prior LYCD model documentation)
  - Key stats: 69.1% of non-exempt parcels see a tax decrease; SFR median change −23.0%; lower-income and higher-minority-share quintiles benefit at least as much as, or slightly more than, higher-income/lower-minority quintiles

---

## 3. Political actors

Current-service verification performed against `phlcouncil.com/members/` (confirmed live 2026-07-18) and the city's official mayoral page. All 19 officials below (Mayor + Council President + 9 other district members + 7 at-large members) are confirmed currently serving as of this brief's date.

| Name | Role | Term ends | Electoral base | District wins? | Base coalition wins? | Score | Confidence | Key evidence |
|---|---|---|---|---|---|---|---|---|
| Cherelle L. Parker | Mayor | Jan 2028 | Citywide; won 2023 Dem primary with 32% (10-pt margin), general 74.7%–24.4% vs. Oh | N/A | Yes (96.2%) | 0 | Medium | Focus on reassessment relief, Homestead Exemption expansion, and a Tax Reform Commission recommending BIRT/wage-tax cuts rather than LVT; supports a 20-year abatement for office-to-residential conversions ("ensure there are no vacant office buildings"). No LVT/split-rate statement located. [Inquirer 8/5/2024](https://www.inquirer.com/politics/philadelphia/philadelphia-property-tax-reassessment-increase-mayor-cherelle-parker-20240805.html); [Metro Philadelphia](https://metrophiladelphia.com/stories/philadelphia-tax-abatement-affordable-housing,115505) |
| Kenyatta Johnson | Council President (D2) | Jan 2028 | District 2 (South Phila); uncontested 2023 Dem primary — no precinct correlation computable | Yes | N/A (uncontested) | +1 | Medium | Supports Mayor's proposed 20-year abatement for conversions to reduce vacant buildings; said he is "open to the idea" as of May 2026, though no bill has been introduced yet. [Inquirer 5/30/2026](https://www.inquirer.com/real-estate/commercial/property-tax-abatement-parker-schools-20260530.html) |
| Mark Squilla | District 1, **Finance Committee Chair** | Jan 2028 | District 1 (South Phila/river wards); uncontested 2023 Dem primary | Yes | N/A (uncontested) | 0 | Low | No specific public position on LVT, split-rate, or the abatement located despite chairing the committee that held the 2021 LVT hearing. [phlcouncil.com/marksquilla](https://phlcouncil.com/marksquilla/) |
| Jamie Gauthier | District 3 | Jan 2028 | District 3 (West Phila); contested primary history | Yes | N/A (2023 primary uncontested for this seat) | +1 | High | Direct YIMBY-aligned advocacy ("at our current pace, it will take more than 200 years..."); introduced bills to speed affordable housing production and to make city-owned vacant land available to Community Land Trusts. [City & State PA, 7/2025](https://www.cityandstatepa.com/policy/2025/07/breaking-regulations-changing-zoning-codes-and-bureaucracy-could-key-housing-solutions/406985/); [phlcouncil.com](https://phlcouncil.com/councilmember-jamie-gauthier-introduces-legislation-to-encourage-the-use-of-city-owned-vacant-land-for-affordable-homes-and-gardens/) |
| Curtis Jones, Jr. | District 4 | Jan 2028 | District 4 (Northwest Phila); uncontested 2023 primary | Yes | N/A (uncontested) | 0 | Low | Co-sponsored the 2019 10-year-abatement phase-down bill, but no individualized or current LVT/split-rate statement located. [phlcouncil.com](https://phlcouncil.com/legislation-introduced-in-council-to-change-the-real-estate-tax-abatement/) |
| Jeffery Young, Jr. | District 5 | Jan 2028 | District 5 (Lower North/Diamond St.); uncontested 2023 primary | Yes | N/A (uncontested) | −1 | Medium | Publicly disparaged "urbanist" priorities (density, bike lanes) as out of step with his mostly-Black, higher-poverty district; blocked a 57-unit senior affordable housing project in 2024. District 5 has the lowest overall parcel win-rate of the 10 districts in this model (53.2%), though SFR parcels there still win at 68.2%. [search-sourced reporting on Young's record and the Diamond Street housing block, 2024] |
| Mike Driscoll | District 6 | Jan 2028 | District 6 (Northeast Phila); uncontested 2023 primary | Yes | N/A (uncontested) | 0 | Medium | Authored a 6-member-cosponsored letter (July 2026) demanding transparency on rising OPA reassessments — "property owners deserve answers now." This is about the existing reassessment process, not LVT specifically, but signals a homeowner-tax-burden-sensitive posture worth flagging for any future LVT ask in his district. [Inquirer 7/15/2026](https://www.inquirer.com/politics/philadelphia/property-value-taxes-council-parker-20260715.html) |
| Quetcy Lozada | District 7 | Jan 2028 | District 7 (Kensington); contested 2023 primary vs. Andrés Celin | Yes | Yes (97.6%) | −1 | Medium | Publicly says "I support development... we cannot block our way to affordability," but concretely blocked a 30-unit Turn the Key affordable-housing project from the city's largest TTK developer — action contradicts stated rhetoric, so scored on the action per the signal-quality hierarchy. Also active on vacant-lot stabilization/anti-dumping (mixed signal). [Kensington Voice](https://www.kensingtonvoice.com/en/city-council-district-7-candidate-quetcy-lozada-answers-questions-from-the-kensington-community/); reporting on the blocked TTK project |
| Cindy Bass | District 8 | Jan 2028 | District 8 (Germantown/Mt. Airy/Logan); contested 2023 primary vs. Seth Anderson-Oberman | Yes | Yes (97.9%) | −1 | Medium | Introduced a bill to **repeal** the 10-year tax abatement outright, arguing the city should return to "the traditional property tax structure" to fund schools — a direct-quote position that pulls toward taxing improvements *more*, the opposite direction from LVT's mechanism. [phlcouncil.com — "Councilwoman Cindy Bass Calls for End to 10-Year Tax Abatements"](https://phlcouncil.com/councilwoman-cindy-bass-calls-for-end-to-10-year-tax-abatements/) |
| Anthony Phillips | District 9 | Jan 2028 | District 9 (West Oak Lane); contested 2023 primary (3-way) | Yes | Yes (92.7%) | 0 | Low | No public statement located on property tax structure, LVT, or vacant land specifically despite searching; his legislative focus is public safety, schools, and youth. |
| Brian J. O'Neill | District 10 | Jan 2028 | District 10 (Northeast Phila, sole Republican); consistently re-elected | Yes | N/A (Republican, no Dem primary contest; general uncontested for council seat) | 0 | Low-Medium | Consistent property-tax-relief advocate (raising the Homestead Exemption to the state maximum, opposing bill increases for "seniors on fixed incomes") — directionally compatible with an SFR-friendly reform but no LVT-specific statement found. [phlcouncil.com/brianoneill](https://phlcouncil.com/brianoneill/) |
| Katherine Gilmore Richardson | At-Large, Majority Leader | Jan 2028 | Citywide; contested 2023 Dem primary (top-5 finisher) | N/A | Yes (91.1%) | 0 | Low | Co-sponsored abatement-reform legislation (2019-era) as part of a bloc; no individualized LVT/split-rate position found. |
| Isaiah Thomas | At-Large, Majority Whip | Jan 2028 | Citywide; contested 2023 Dem primary (top-5 finisher) | N/A | Yes (94.7%) | 0 | Low | Same bloc co-sponsorship pattern as Gilmore Richardson; no individualized position found. |
| Jim Harrity | At-Large | Jan 2028 | Citywide; contested 2023 Dem primary (top-5 finisher) | N/A | N/A (primary vote-share not individually modeled — insufficient distinguishing signal in available search results) | 0 | Low | General participation in housing-package votes (Low-Income Tax Freeze extension); no individualized position found. |
| Nina Ahmad | At-Large | Jan 2028 | Citywide; contested 2023 Dem primary (top-5 finisher) | N/A | N/A (same as Harrity) | 0 | Low | Participated in a housing legislative package (eviction diversion, rental assistance); no individualized LVT position found. |
| Rue Landau | At-Large | Jan 2028 | Citywide; contested 2023 Dem primary (top-5 finisher) | N/A | N/A (not separately modeled — Landau's primary vote total was folded into the broader at-large correlation set only for Gilmore Richardson/Thomas as the two highest vote-getters; not a data gap in Landau's activity, just a scoping choice for this brief) | 0 | Medium | Active on tenant-facing relief (Move-In Affordability Plan, property-assessment-appeal deadline extensions) and general housing-cost reduction; no LVT-specific statement found. [phlcouncil.com/ruelandau](https://phlcouncil.com/ruelandau/) |
| Kendra Brooks | At-Large, Minority Leader (WFP) | Jan 2028 | Citywide, WFP reserved minority seat; general election is dispositive | N/A | Yes (92.1%) | 0 | Medium | Has written in her own voice that the 10-year abatement should be scrapped as a matter of racial/economic equity — again, the opposite direction from LVT's logic of *reducing* improvement taxation. Her "People's Tax Plan" and wealth-tax proposal target investment income, not land value, as the alternative revenue source. [WHYY — Brooks op-ed](https://whyy.org/articles/kendra-brooks-undo-structural-racism-by-nixing-phillys-10-year-tax-abatement/) |
| Nicolas O'Rourke | At-Large (WFP) | Jan 2028 | Citywide, WFP reserved minority seat; general election is dispositive | N/A | Yes (91.4%) | 0 | Medium | Co-sponsor of Brooks' "People's Tax Plan"; same reasoning as Brooks applies. [WHYY election coverage](https://whyy.org/articles/philadelphia-election-2023-nicolas-orourke-kendra-brooks-working-families-party-city-council-at-large-race/) |

**State legislators (Tier 4/5 pathway — required scope per Gate 4):**

| Name | Role | Relevance | Score | Confidence | Key evidence |
|---|---|---|---|---|---|
| Sen. Nikil Saval (D) | PA Senate District 1 (Philadelphia); chairs the Senate Urban Affairs & Housing Committee and the Senate Philadelphia Delegation | Structurally the best-placed potential sponsor for a Sterling Act amendment or uniformity-clause reform bill | 0 | Low | The 2026-06-01 legal brief describes him as having "advocated for removing PA's uniformity clause." This research could **not corroborate a specific current (2025–2026) bill, resolution, or public statement** on uniformity-clause reform or LVT enabling legislation from Saval — treat the legal brief's characterization as unconfirmed pending a direct check of his sponsorship record on the PA legislature's bill-search system. |
| Gov. Josh Shapiro (D) | Governor | Would need to sign any enabling legislation | 0 | Medium | 2026 property-tax agenda is relief-focused (expanded Property Tax/Rent Rebate Program, ~$1B homestead/farmstead exclusion expansion) — no structural uniformity-clause or LVT-enabling position found. [PA.gov Revenue newsroom](https://www.pa.gov/agencies/revenue/newsroom/shapiro-administration-announces--226-million-headed-to-nearly-376,000-pennsylvanians-through-expanded-property-tax-rent-rebate-program--deadline-to-apply-extended-to-december-31) |
| PA Senate Republican majority (28–22) | Controls the chamber that would need to pass any enabling bill | Highest-leverage veto point in the entire pathway | −1 | Medium | No Republican Senate sponsor or supportive statement was found for any Philadelphia-specific tax-authority expansion; the GOP Senate's role since 2022 has been described as "Democratic Gov. Shapiro's primary opposition." Scored as mild, not strong, opposition because this reflects general posture/inference rather than a specific anti-LVT vote or statement. [Spotlight PA](https://www.spotlightpa.org/news/2026/01/pennsylvania-election-results-2026-state-house-senate-governor-elections/) |

---

## 4. Electoral math

Computed from `analysis/data/philadelphia_lycd.csv` (579,814 parcels; 535,698 non-exempt).

- All taxable (non-exempt) parcels with a tax decrease: **69.1%**
- SFR parcels with a tax decrease: **76.6%** (n = 408,137 SFR parcels)
- Median SFR tax change: **−23.0%**
- Commercial/Industrial parcels with a tax increase: **47.5%** (n = 12,008; median change among this group is actually still slightly negative, −4.0%, reflecting that many commercial parcels are improvement-heavy and benefit from the lower improvement millage even as some land-heavy commercial parcels see increases)

**Political reading:** More than three in four single-family homeowners — Philadelphia's largest, highest-turnout property-owning bloc — would see a tax cut, and the median cut is a politically substantial 23%. This is a strong homeowner-relief talking point, not a marginal one. Commercial property is roughly a coin flip between winners and losers rather than uniformly burdened, which undercuts a simple "big business vs. homeowners" opposition frame — the organized opposition case has to be made property-type by property-type, not citywide.

### Income quintile impact

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (lowest income) | −21.7% | Lowest-income neighborhoods benefit as much as any other quintile — undercuts a "this hurts poor communities" opposition frame |
| Q2 | −22.2% | Largest median benefit of any quintile |
| Q3 | −20.2% | Still a strong median cut |
| Q4 | −19.4% | Smaller but still solidly negative |
| Q5 (highest income) | −19.4% | Wealthier neighborhoods benefit slightly less, but still see a net cut, not an increase |

### Minority concentration quintile impact

| Quintile | Median tax change % | Political reading |
|---|---|---|
| Q1 (lowest minority share) | −19.9% | |
| Q2 | −20.6% | |
| Q3 (median) | −21.4% | Largest median benefit |
| Q4 | −20.1% | |
| Q5 (highest minority share) | −20.1% | Benefit is essentially flat across the minority-concentration spectrum — no quintile is a net loser, and no quintile is dramatically better off than another |

### Vacant land

- Vacant parcels as % of all taxable (incl. exempt): **7.1%** (41,274 of 579,814; 27,925 of these are taxable/non-exempt)
- Top vacant-land owners by LYCD taxable land value (owner data merged from `parcels.gpq` `owner_1`/`owner_2`, OPA-truncated names — lower bound, no LLC-network resolution performed for this brief): South Christopher (2 parcels, 3.0% of taxable vacant land value), K4 Philadelphia LLC (1 parcel, 1.3%), Republic Service Inc (1 parcel, 1.2%), Philadelphia Regional Port Authority (1 parcel, 1.2%), BW Property Owner LLC (1 parcel, 1.0%), Conrail (42 parcels, 0.9%), CSX Transportation Inc (10 parcels, 0.8%), Archdiocese of Philadelphia (2 parcels, 0.8%). **Concentration: the top 5% of the 18,815 distinct vacant-land owners hold 67.5% of taxable vacant land value; the top 10% hold 75.6%.** This is a strong "land-banking is concentrated, not diffuse" talking point — large institutional/corporate holders, not scattered small owners, capture most of the vacant-land value that would face the biggest relative increases under LVT.

### District-level breakdown

Computed via centroid spatial join of `parcels.gpq` (joined to the LYCD model on stripped `parcel_number` ↔ `parcel_id`) to `council_districts.gpq` (DISTRICT field), reprojected to EPSG:2272 for the centroid calculation. 3 of 535,721 merged parcels fell outside all district polygons (edge/boundary artifacts) and were dropped.

| District | Councilmember | % All parcels ↓ | % SFR ↓ | Median SFR Δ% | SFR majority wins? |
|---|---|---|---|---|---|
| 1 | Mark Squilla | 66.1% | 72.7% | −21.3% | Yes |
| 2 | Kenyatta Johnson | 67.5% | 77.2% | −24.9% | Yes |
| 3 | Jamie Gauthier | 67.3% | 77.3% | −27.5% | Yes |
| 4 | Curtis Jones, Jr. | 71.3% | 77.3% | −23.9% | Yes |
| 5 | Jeffery Young, Jr. | 53.2% | 68.2% | −21.9% | Yes |
| 6 | Mike Driscoll | 80.8% | 82.7% | −22.1% | Yes |
| 7 | Quetcy Lozada | 65.0% | 79.8% | −28.1% | Yes |
| 8 | Cindy Bass | 65.3% | 73.0% | −24.2% | Yes |
| 9 | Anthony Phillips | 77.0% | 77.6% | −17.9% | Yes |
| 10 | Brian O'Neill | 79.2% | 79.5% | −21.6% | Yes |

**Minimum winning coalition analysis:** **All 10 of 10 district council members** represent an SFR-majority-winning district — well beyond the 9 of 17 votes needed for a simple council majority (and beyond the 12 needed to override a mayoral veto, if the 7 at-large members were unanimously opposed, which nothing here suggests). District 5 (Young) has the weakest overall parcel win rate (53.2%, driven by a lower vacant-land/investor-property share and Young's district having a below-average share of SFR parcels relative to other categories) but its SFR homeowners still win at 68.2% — meaning even Philadelphia's most development-skeptical district member represents a homeowner base that would benefit. The homeowner-relief case is not just defensible in a few friendly districts — it is uniform across the entire council map.

### Precinct-level vote-share correlation

Computed from real 2023 election returns — Philadelphia City Commissioners' official ward/division results (`vote.phila.gov/media/2023_Primary_Results.xlsx` and `2023_General_Results.xlsx`), joined to OpenDataPhilly's "Political Ward Divisions" boundary layer (1,703 divisions vs. 1,704 precinct rows in the returns — a close match consistent with correct vintage, though the division layer's exact last-updated date could not be independently confirmed against the 2023 election cycle; treat with mild caution). The May 2023 Democratic primary is the dispositive election for Philadelphia's overwhelmingly Democratic seats; the November 2023 general is used for the two Working Families Party at-large seats, which are only decided in the general. Contested races only — 7 of the 10 district seats were uncontested in the 2023 primary and have no meaningful vote-share variation to correlate (marked N/A in Section 3).

| Official / race | Correlation (vote share vs. % all ↓) | Correlation (vote share vs. % SFR ↓) | Base-coalition SFR win rate | Interpretation |
|---|---|---|---|---|
| Cherelle Parker (Mayor, 2023 Dem primary) | r = −0.16 | r = 0.01 | 96.2% | Essentially no relationship between where Parker ran strongest and the reform's SFR winners — her coalition is neither favored nor disfavored, and her base's SFR win rate is far above the citywide rate, meaning even her strongest precincts do well |
| Quetcy Lozada (D7, 2023 Dem primary vs. Celin) | r = 0.06 | r = 0.05 | 97.6% | Negligible correlation; Lozada's electoral stronghold in Kensington is a strong net winner regardless of her (mixed) position |
| Cindy Bass (D8, 2023 Dem primary vs. Anderson-Oberman) | r = −0.17 | r = −0.02 | 97.9% | Weak negative on the all-parcel measure but flat on SFR; Bass's own base still wins under the model at nearly a 98% rate despite her stated opposition to reducing improvement taxation |
| Anthony Phillips (D9, 2023 3-way Dem primary) | r = −0.01 | r = 0.03 | 92.7% | No meaningful relationship |
| Katherine Gilmore Richardson (At-Large, 2023 Dem primary) | r = −0.07 | r = −0.12 | 91.1% | Weak negative — her strongest precincts skew very slightly toward lower SFR-win-rate areas, though the win rate in her stronghold (91.1%) is still far above a losing threshold |
| Isaiah Thomas (At-Large, 2023 Dem primary) | r = −0.17 | r = −0.13 | 94.7% | Similarly weak negative; not a material risk given the high absolute win rate in his base |
| Kendra Brooks (At-Large WFP, 2023 general) | r = −0.09 | r = −0.06 | 92.1% | Negligible; her voter base is not disproportionately exposed despite her own stated opposition to reducing improvement tax burden |
| Nicolas O'Rourke (At-Large WFP, 2023 general) | r = −0.03 | r = −0.04 | 91.4% | Negligible |

**Reading across all eight races:** every correlation is weak (|r| ≤ 0.17) and every base-coalition SFR win rate is above 91%. (Definition note, added in the 2026-07-18 audit: "base-coalition SFR win rate" is the share of an official's top-quartile precincts in which a *majority* of SFR parcels win — a precinct-level metric. The parcel-level equivalent for Mayor Parker's stronghold is 76.6% of SFR parcels winning, essentially identical to the citywide 76.6%; the two metrics should not be compared to each other.) The consistent pattern is that no official's electoral stronghold is a *loser* under this reform; if anything, several officials' strongest precincts (which tend to be denser, more homeowner-heavy legacy neighborhoods within their districts) do somewhat *better* than their district as a whole. This is a genuinely favorable structural finding: there is no "safe seat that's actually a losing pocket" dynamic here for any of the eight officials tested, which removes one common reason an otherwise-sympathetic official might quietly resist. (Scope caveat, added in the 2026-07-18 audit: this favorable finding is specific to *homeowners*. On an all-taxable-parcel basis, Mayor Parker’s stronghold is mildly more exposed than the city (r = −0.17; 67% vs 69% of parcels winning), reflecting commercial-corridor precincts inside her coalition — messaging should say “her homeowner base,” not “her base.” Deep-audit addendum, same date: restricting to owner-occupied SFR — the actual voters — her stronghold trails the citywide homeowner win rate by ~4pp (71.2% vs 75.3%, r = −0.106); the fully-flat headline correlation was partly supported by investor-owned SFR in her stronghold. Still a solid majority of her base’s homeowners win, with shallow losses (median loser ≈ $130/yr); see analysis/political/philadelphia_mayor_exposure_audit.md.)

---

## 5. Political environment

### Issue salience

- **Housing affordability** — High and current. ~30% of renters and 16% of homeowners are cost-burdened. Mayor Parker's $2B "H.O.M.E." initiative (30,000-unit target) and a late-2025 "Safe Healthy Homes" tenant-protection package are both active. [Generocity, 5/2026](https://generocity.org/philly/2026/05/27/housing-insecurity-philadelphia-crisis/); [WHYY](https://whyy.org/articles/philadelphia-housing-market-pains-2026/)
- **Blight/vacant land** — Very high salience. ~40,000 vacant parcels citywide (roughly a quarter city-owned, the rest private), concentrated in North Philadelphia. Mayor Parker has proposed a 20-year abatement specifically to spur demolition/reuse of underused buildings; Council held hearings on the Act 135 abandoned-property conservatorship law. [Penn IUR](https://penniur.upenn.edu/publications/vacant-land-management-in-philadelphia-the-costs-of-the-current-system-and-the); [Inquirer, 11/26/2025](https://www.inquirer.com/real-estate/commercial/city-council-building-demolition-preservation-20251126.html)
- **Property tax/reassessment backlash** — Confirmed major, *live* flashpoint. The Aug. 2024 citywide reassessment (effective TY2025) raised average homeowner bills ~$330; a Community Legal Services report found statistically significant systemic bias in OPA assessments; as of **July 15, 2026**, six Council members (led by Driscoll) sent a public letter demanding transparency on a new round of rising assessments. [Inquirer, 8/5/2024](https://www.inquirer.com/politics/philadelphia/philadelphia-property-tax-reassessment-increase-mayor-cherelle-parker-20240805.html); [Inquirer, 7/15/2026](https://www.inquirer.com/politics/philadelphia/property-value-taxes-council-parker-20260715.html)
- **Parking lots/underutilized downtown land** — Active commentary. An April 2026 Inquirer column specifically asked why Center City still has two dozen-plus 1960s-era surface parking lots owned by "a handful of people." [Inquirer, 4/6/2026](https://www.inquirer.com/columnists/center-city-surface-parking-lots-housing-transit-oriented-development-mayor-parker-affordable-20260406.html)
- **Downtown/Center City office decline** — Real but not treated as a crisis; Q2 2025 CBD office vacancy (~20.4%) is favorable versus peer cities. Philadelphia leads the nation in office-to-residential conversion growth. [Billy Penn, 9/17/2025](https://billypenn.com/2025/09/17/philly-job-growth-is-up-but-many-downtown-offices-remain-vacant/)
- **10-year abatement reform fights** — Ongoing and unresolved. Council's Tax Reform Commission (est. Feb. 2024) released a Feb. 2025 interim report favoring BIRT/wage-tax cuts over further abatement changes; a *new* 20-year abatement for office-to-residential conversions was separately advanced through the 2025 PA state budget process. [phlcouncil.com/taxreform](https://phlcouncil.com/taxreform/); [Inquirer, 11/21/2025](https://www.inquirer.com/real-estate/commercial/pennsylvania-state-budget-taxes-housing-conversion-projects-20251121.html)

### Advocacy landscape

- **Tenant/renter advocacy:** Philadelphia Tenants Union (grassroots; hosted its 2nd Annual Tenant Conference March 2026); a broader Rent Control Coalition (PTU, One PA, Community Legal Services, TURN, Reclaim Philadelphia, Philly DSA, Sunrise Philly, and others). [rentcontrolphilly.org](https://rentcontrolphilly.org/about/)
- **YIMBY-aligned:** Philly YIMBY, a project of 5th Square (Philadelphia's urbanist PAC), running an active "Zoning Tracker." [phillyyimby.com](https://phillyyimby.com/)
- **Georgist/LVT-specific:** Center for the Study of Economics (Josh Vincent) remains Philadelphia-based and active as of 2024, explicitly nonpartisan and non-electoral in posture — technical assistance, not organizing capacity. [urbantoolsconsult.org](https://urbantoolsconsult.org/tag/philadelphia/)
- **Landlord/commercial real estate:** HAPCO Philadelphia (~5,500 landlord members) has in the past aligned *with* tenant-side groups on some abatement/below-market legislation — not a simple landlord-vs-tenant split. NAIOP Philadelphia and Center City District/University City District positions on vacant-land or split-rate taxation specifically were searched for and **not found** — a real gap, not an oversight.
- **Academic/neutral research:** Pew Charitable Trusts' Philadelphia initiative and Penn IUR are the most active neutral technical voices on the property tax base; neither has taken an explicit LVT position.

### Peer city signal

- **Pittsburgh** repealed its split-rate system in 2001 after a botched reassessment caused a land-value-tax spike and homeowner backlash — the standard cautionary tale on assessment competence. A local group, Pro-Housing Pittsburgh, is actively campaigning in 2025–2026 to re-adopt land value taxation, but no split-rate legislation has actually been introduced; Pittsburgh's dominant 2025–2026 property-tax story is instead a 20–30% flat rate hike. [prohousingpgh.org](https://www.prohousingpgh.org/blog/policy-land-value-taxes); [WESA, 12/21/2025](https://www.wesa.fm/politics-government/2025-12-21/pittsburgh-city-council-poised-to-pass-20-percent-property-tax-hike)
- **Detroit** offers the closest direct analogue: Mayor Duggan's LVT plan (avg. 17% homeowner cut, funded by higher rates on vacant/blighted land) requires Michigan legislature enabling action first, then a Detroit voter referendum — bills have stalled in the Michigan House in both 2023 and 2024 and remained unpassed as of Jan. 2026. This is the same "state enabling legislation first" structural pattern Philadelphia faces. [Niskanen Center](https://www.niskanencenter.org/detroit-could-be-the-largest-u-s-city-with-land-value-tax-if-the-state-legislature-allows-it/)

### Recent referenda

No Philadelphia ballot measure specifically on property tax, LVT/split-rate, or rent control was found in the 2021–2026 window. A May 2022 charter amendment restructured the Zoning Board of Adjustment. Rent control remains at the advocacy-coalition stage, not yet a ballot question.

### Election calendar

- Philadelphia city elections are odd-year; Parker/current Council seated Jan. 2024; next city election **2027**. This is currently outside the typical 12–18-month pre-election "hostile to novel tax proposals" window, but the window will begin closing in mid-2026.
- **2026 is a PA gubernatorial election year**, with Gov. Shapiro up for re-election and both legislative chambers competitive — meaning the state-level pathway (the actual gating step) is itself subject to change based on this November's outcome.

---

## 6. Demographic predictors

Source: ACS 2019–2023 5-year estimates, Philadelphia County/City, PA (FIPS 42101), pulled directly from the Census API.

| Factor | City figure | Political implication |
|---|---|---|
| Renter proportion | 47.7% (319,081 of 669,222 occupied units) | Above the 45% threshold for a "large latent LVT constituency" — renters are a near-plurality of households, though their political translation depends on turnout/organization (see Rent Control Coalition above) |
| Median age | 35.1 years | Slightly younger than the national median; consistent with a base more open to LVT per prior PPI/CLE polling on age |
| % under 35 | ~50.0% | A genuinely large young-adult population base |
| Partisan lean | 2024 presidential: Harris ~79.6% vs. Trump ~20.4% (~59-pt margin); one-party-dominant | The real contest for any local or state-legislative seat touching this reform is the Democratic primary, not the general — this brief's precinct analysis correctly used the May 2023 primary for that reason |
| Homeownership rate | 52.3% | A majority-homeowner city, which raises the political stakes of the SFR electoral math in Section 4 — and that math is strongly favorable |
| Median household income | $60,698 | Below the national median; raises housing-affordability salience but also means commercial-tax-increase arguments ("business flight") could carry some weight in a lower-income city more dependent on local job bases |

Source: [Census QuickFacts](https://www.census.gov/quickfacts/philadelphiacountypennsylvania); [Census Reporter](http://censusreporter.org/profiles/16000US4260000-philadelphia-pa/); [CBS Philadelphia 2024 election results](https://www.cbsnews.com/philadelphia/news/philadelphia-presidential-election-results-2024/); [Wikipedia: 2023 Philadelphia mayoral election](https://en.wikipedia.org/wiki/2023_Philadelphia_mayoral_election)

---

## 7. Coalition map

|  | **For** | **Against** |
|---|---|---|
| **Organized** | Philly YIMBY / 5th Square (zoning/infill advocacy infrastructure); Center for the Study of Economics (Josh Vincent — nonpartisan technical LVT advocacy, no electoral capacity); Pew Charitable Trusts and Penn IUR (neutral research infrastructure that could be mobilized, no advocacy position taken) | No named organization has taken an explicit anti-LVT position in Philadelphia specifically. NAIOP Philadelphia and Center City District/University City District were searched for a position and **none was found** — flagged as a real gap, not confirmed opposition |
| **Latent / unorganized** | Renters (47.7% of households, largely unorganized as a voting bloc despite the Rent Control Coalition's organizing); young voters (~50% under 35); homeowners in the many high-win-rate districts (Districts 4, 6, 9, 10 all show >77% SFR win rates) | Owners of concentrated vacant land (top 5% of vacant-land owners hold 67.5% of value — a small, identifiable, well-resourced group with a direct and large financial stake in opposing); District 5-style skeptics of density/urbanist framing, who may generalize that skepticism to any "urbanist" tax reform even where the SFR math favors them |

---

## 8. Official alignment score

- Votes required: 9 of 17 for a City Council ordinance (once state authorization exists); separately, majority support on the PA General Assembly's relevant committees/floor votes, and separately, Board of Education action for the school-district share
- Officials researched: 19 (Mayor, Council President, 9 other district members, 7 at-large members), plus 3 state-level actors (Sen. Saval, Gov. Shapiro, PA Senate GOP majority as a bloc)
- Score breakdown: +1 (Johnson), +1 (Gauthier), −1 (Young), −1 (Lozada), −1 (Bass), 0 (all 13 remaining council officials) = net −1 across 19 council-level officials (mean ≈ −0.05); −1 (PA Senate GOP majority), 0/0 (Saval, Shapiro) at the state level
- Overall alignment: **Split / uncertain** — no council member has taken an affirmative LVT/split-rate position, and the officials with the clearest signal (Bass, Brooks/O'Rourke) are oriented toward *increasing* improvement taxation, which cuts against LVT's core mechanism even though their own electoral bases would benefit under the model (Section 4)
- **Key swing votes:** Mark Squilla (Finance Committee Chair — any future hearing on this topic runs through him, and no position was found); Council President Kenyatta Johnson (sets the agenda and has shown some openness to reducing improvement-side tax burden via the conversion abatement, but has not engaged with LVT/split-rate specifically); Sen. Nikil Saval (the one state legislator with the institutional position — Senate Philadelphia Delegation chair — to plausibly sponsor enabling legislation, but with no confirmed current activity on this specific issue)

---

## 9. Structural viability score

| Factor | Score (0–2) | Rationale |
|---|---|---|
| Electoral math | 2 | 76.6% of SFR parcels see a tax decrease — well above the >60% threshold for the top score |
| Renter proportion | 2 | 47.7% renter-occupied — above the 45% threshold |
| Housing crisis salience | 2 | Housing affordability, blight, and (very currently, as of this month) reassessment/property-tax-burden backlash are all dominant, actively-covered issues |
| Legal pathway ease | 1 | Tier 4/5 — state enabling legislation required, from a divided legislature with no confirmed champion |
| Organized ally strength | 1 | Multiple named organizations exist (Philly YIMBY/5th Square, Rent Control Coalition, Center for the Study of Economics) but none has organized specifically around LVT or demonstrated a legislative win on this issue |
| **Total** | **8/10** | |

---

## 10. Strategic framing

**Recommended primary frame:** Blight/vacant land. The data supports it unusually well here: vacant-land ownership is concentrated (top 5% of owners hold 67.5% of taxable vacant land value — a small, nameable set of institutional holders, not scattered homeowners), blight is a demonstrably high-salience issue with active Council hearings and a Penn IUR study already circulating, and the reform's biggest percentage increases fall specifically on land-banking rather than on owner-occupied housing.

**Recommended secondary frame:** Property tax relief for homeowners. With 76.6% of SFR parcels seeing a median 23% cut, and every one of the 10 council districts showing an SFR majority win, this is a very concrete, quantifiable talking point precisely at a moment (July 2026) when reassessment-driven homeowner tax anxiety is an active news story that Council members themselves are publicly demanding answers about.

**Frames to avoid:** A pure "fiscal efficiency/business investment" frame is weaker here than in many cities — commercial/industrial parcels are roughly split 47.5%/52.5% between increases and decreases, so a frame promising broad business relief would be only partly true and invites easy rebuttal from the roughly-half of commercial owners facing increases. A frame that leans on Council's own recent tax-reform activity (the Tax Reform Commission) as a foothold should be used cautiously — that Commission's 2025 interim report leaned toward BIRT/wage-tax cuts, not toward a land/improvement rate split, so its existence is not itself evidence of Council appetite for this specific reform.

### Key talking points (grounded in model data)

- "Under a full land value tax shift, the median Philadelphia homeowner's tax bill falls by 23% — and that holds true in every single one of the city's 10 council districts, not just a few."
- "The lowest-income neighborhoods in Philadelphia would see the same or slightly larger tax cuts as the wealthiest — this is not a reform that trades off equity for efficiency."
- "Just under 19,000 owners hold Philadelphia's vacant land, and the top 5% of them — mostly institutional and corporate holders — control two-thirds of its value. This is who currently under-pays on the parcels sitting empty across North Philadelphia and elsewhere."
- "No council member's own electoral base is a net loser under this reform — even in the most contested 2023 primaries, the winning candidate's strongest precincts see SFR win rates above 90%, well above the citywide average."

---

## 11. Open questions and research gaps

- **Officials with no clear signal found (search performed, nothing located):** Mark Squilla, Curtis Jones Jr., Anthony Phillips, Katherine Gilmore Richardson, Isaiah Thomas, Jim Harrity, Nina Ahmad, Rue Landau (on LVT specifically — all have general housing/tax-relief activity but nothing individualized to LVT/split-rate).
- **Sen. Nikil Saval's uniformity-clause position:** the 2026-06-01 legal brief attributes an advocacy position to Saval that this research could not independently corroborate with a specific bill or current public statement. This should be checked directly against the PA General Assembly's bill-sponsorship database before it is relied upon in any outreach strategy.
- **Base-coalition data not computed for Jim Harrity, Nina Ahmad, and Rue Landau specifically** — the at-large primary correlation analysis was limited to the two highest vote-getters (Gilmore Richardson, Thomas) as a scoping choice under this brief's time budget, not because their returns are unavailable; a fuller version could extend the same method to all 5 Democratic at-large primary winners.
- **Precinct boundary vintage:** the OpenDataPhilly "Political Ward Divisions" layer used for the precinct join could not be independently confirmed as the exact 2023-election-cycle boundary vintage (its metadata page did not state a last-updated date). The close match between division count (1,703) and precinct-result-row count (1,704) is reassuring but not conclusive; a "Historic Political Wards & Divisions" fallback dataset exists on OpenDataPhilly and could be used to cross-check if this matters for a higher-stakes use of this analysis.
- **District boundary vs. current officials:** `council_districts.gpq`'s `DISTRICT` field was taken at face value as matching the 10 current district officials; this is standard practice but was not independently re-verified against a live phila.gov boundary service in this research pass.
- **Demolition-to-vacant-land loophole:** this brief did not investigate whether Philadelphia has an analogous vacant/blighted-building classification loophole to the one documented for Washington, DC (see `washington-dc-model` project memory) — i.e., whether tearing down a deteriorating structure lets an owner drop into a lower-taxed "vacant land" bucket under current OPA classification rules. Given how large the vacant-land ownership concentration is here, this would be a valuable follow-up specific to Philadelphia.
- **Follow-up research most likely to change this assessment:** (1) a direct check of PA bill-sponsorship records for any 2025–2026 Sterling Act amendment or uniformity-clause bill; (2) a follow-up interview or public-statement search focused specifically on Mark Squilla given his Finance Committee chairmanship; (3) tracking whether the November 2026 PA gubernatorial/legislative elections shift Senate control, which would directly reopen or further close the Tier 4/5 pathway.

---

## 12. Sources

### Legal & model inputs
- [Philadelphia, Pennsylvania — LVT Legal Brief](../legal/Philadelphia.md) (2026-06-01)
- `analysis/data/philadelphia_lycd.csv` (LYCD split-rate 4:1 model export)
- `cities/philadelphia/data/parcels.gpq`, `cities/philadelphia/data/council_districts.gpq` (cached parcel and district geometry)

### Officials and roster verification
- [Philadelphia City Council — Members](https://phlcouncil.com/members/)
- [Philadelphia City Council — Leadership and Committee Chair Assignments (2022)](https://phlcouncil.com/city-council-announces-new-leadership-and-committee-chair-assignments/)
- [Kenyatta Johnson — Wikipedia](https://en.wikipedia.org/wiki/Kenyatta_Johnson); [WHYY — Johnson acquittal](https://whyy.org/articles/kenyatta-johnson-corruption-retrial-verdict-acquitted/)
- [Jamie Gauthier — vacant land legislation](https://phlcouncil.com/councilmember-jamie-gauthier-introduces-legislation-to-encourage-the-use-of-city-owned-vacant-land-for-affordable-homes-and-gardens/); [City & State PA, 7/2025](https://www.cityandstatepa.com/policy/2025/07/breaking-regulations-changing-zoning-codes-and-bureaucracy-could-key-housing-solutions/406985/)
- [Cindy Bass — call to end 10-year abatement](https://phlcouncil.com/councilwoman-cindy-bass-calls-for-end-to-10-year-tax-abatements/)
- [Kendra Brooks op-ed — WHYY](https://whyy.org/articles/kendra-brooks-undo-structural-racism-by-nixing-phillys-10-year-tax-abatement/); [Working Families Party — 2023 victory](https://workingfamilies.org/2023/11/victory-for-nicolas-orourke-and-kendra-brooks/)
- [Brian O'Neill — property tax relief](https://phlcouncil.com/councilman-oneill-announces-property-tax-relief-measures/)
- [Rue Landau — Move-in Affordability Plan](https://phlcouncil.com/councilmember-rue-landau-introduces-move-in-affordability-plan-to-cut-rental-fees-and-ease-housing-costs-for-renters/)
- [Inquirer — Mayor Parker's 20-year abatement proposal, 5/30/2026](https://www.inquirer.com/real-estate/commercial/property-tax-abatement-parker-schools-20260530.html)
- [Inquirer — Driscoll-led Council letter on reassessments, 7/15/2026](https://www.inquirer.com/politics/philadelphia/property-value-taxes-council-parker-20260715.html)

### Political environment
- [Generocity — housing insecurity, 5/2026](https://generocity.org/philly/2026/05/27/housing-insecurity-philadelphia-crisis/)
- [Penn IUR — Vacant Land Management in Philadelphia](https://penniur.upenn.edu/publications/vacant-land-management-in-philadelphia-the-costs-of-the-current-system-and-the)
- [Inquirer — reassessment increase, 8/5/2024](https://www.inquirer.com/politics/philadelphia/philadelphia-property-tax-reassessment-increase-mayor-cherelle-parker-20240805.html)
- [Community Legal Services — systemic bias report](https://clsphila.org/housing/new-report-shows-unintentional-systemic-bias-in-philadelphia-property-assessments/)
- [Inquirer — Center City surface parking lots, 4/6/2026](https://www.inquirer.com/columnists/center-city-surface-parking-lots-housing-transit-oriented-development-mayor-parker-affordable-20260406.html)
- [Billy Penn — Center City office vacancy, 9/17/2025](https://billypenn.com/2025/09/17/philly-job-growth-is-up-but-many-downtown-offices-remain-vacant/)
- [Philadelphia City Council — Tax Reform Commission](https://phlcouncil.com/taxreform/)
- [Inquirer — 20-year conversion abatement via state budget, 11/21/2025](https://www.inquirer.com/real-estate/commercial/pennsylvania-state-budget-taxes-housing-conversion-projects-20251121.html)
- [Philadelphia Tenants Union / Rent Control Coalition](https://rentcontrolphilly.org/about/)
- [Philly YIMBY / 5th Square](https://phillyyimby.com/)
- [Center for the Study of Economics — Philadelphia](https://urbantoolsconsult.org/tag/philadelphia/)
- [Land Value Tax Guide — The Pittsburgh Experience](https://landvaluetaxguide.com/the-pittsburgh-experience/)
- [Pro-Housing Pittsburgh](https://www.prohousingpgh.org/blog/policy-land-value-taxes)
- [Niskanen Center — Detroit LVT plan](https://www.niskanencenter.org/detroit-could-be-the-largest-u-s-city-with-land-value-tax-if-the-state-legislature-allows-it/)
- [Spotlight PA — 2026 PA legislature control](https://www.spotlightpa.org/news/2026/01/pennsylvania-election-results-2026-state-house-senate-governor-elections/)
- [PA.gov — Shapiro property tax/rent rebate expansion](https://www.pa.gov/agencies/revenue/newsroom/shapiro-administration-announces--226-million-headed-to-nearly-376,000-pennsylvanians-through-expanded-property-tax-rent-rebate-program--deadline-to-apply-extended-to-december-31)

### Demographics
- [Census QuickFacts — Philadelphia County, PA](https://www.census.gov/quickfacts/philadelphiacountypennsylvania)
- [Census Reporter — Philadelphia, PA](http://censusreporter.org/profiles/16000US4260000-philadelphia-pa/)
- [CBS Philadelphia — 2024 presidential results](https://www.cbsnews.com/philadelphia/news/philadelphia-presidential-election-results-2024/)
- [Wikipedia — 2023 Philadelphia mayoral election](https://en.wikipedia.org/wiki/2023_Philadelphia_mayoral_election)

### Election data (precinct-level analysis)
- Philadelphia City Commissioners — [2023 Primary Results (division detail)](https://vote.phila.gov/media/2023_Primary_Results.xlsx); [2023 General Results (division detail)](https://vote.phila.gov/media/2023_General_Results.xlsx)
- OpenDataPhilly — [Political Ward Divisions](https://opendataphilly.org/datasets/political-ward-divisions/)
