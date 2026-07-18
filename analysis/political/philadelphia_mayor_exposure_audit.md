# Deep audit: the chain from OPA data to "LVT is politically palatable for Mayor Parker"

**Date:** 2026-07-18 (supersedes the same-day implementation audit; implementation findings carried forward)
**Scope:** Every assumption, logic step, and implementation detail in the chain from raw parcel data to the claim that Mayor Parker's electoral base is not disproportionately exposed to LVT reform losses. Sources audited: the four model exports, `cities/philadelphia/model_lycd.ipynb` construction, the 2023 election pipeline, `scripts/map_philadelphia_mayor_exposure.py` / `scatter_…`, and the two political briefs (`philadelphia_lycd{,_post_abatement}.md`).

## Bottom line

**The claim survives, in a sharpened form.** The defensible statement is:

> *A solid majority of the homeowners in Mayor Parker's electoral base win under the modeled reform, under every land-value structure tested (OPA splits, LYCD zone-price, FHFA market-calibrated tract shares); where her base's homeowners lose, the losses are shallow (median ≈ $130/yr, 90th percentile ≈ $500/yr — an order of magnitude smaller than losses elsewhere in the city); and the large dollar losers inside her base are overwhelmingly vacant-land holders, the policy's intended target.*

The claims that do **not** survive unqualified:
1. **"Her base tracks the citywide average exactly" was partly an artifact of investor-owned homes.** Restricting to owner-occupied homes (the actual voters), her base trails the citywide homeowner win rate by ~4pp under LYCD at 4:1 (71.2% vs 75.3%), significant but modest (r = −0.106). The flat headline correlation was propped up by investor-owned SFR in her stronghold winning at 87.6%.
2. **"Her base is safe" must be scoped to homeowners.** On an all-taxable-parcel basis her stronghold is mildly more exposed (r = −0.166; 67% vs 69%).
3. **The result is ratio- and land-share-sensitive in a consistent direction:** her base's relative exposure grows as the split steepens (2:1 → 4:1) and as the assumed land share rises (15% → 30%), but never drops below majority-winner status anywhere in the tested space.

## Per-link verdict table

Verdicts: **VERIFIED** (checked, correct) · **ROBUST** (conclusion stable under perturbation) · **WEAKENED** (claim survives but smaller/qualified) · **ASSUMPTION** (untestable from within; flagged as scope condition).

| # | Link | Verdict | Key evidence |
|---|------|---------|--------------|
| 1 | OPA assessed values as ground truth | ASSUMPTION (adjudicated) | OPA and LYCD disagree on the sign of her base's exposure (r = −0.33 vs ≈0). Her strongholds are the epicenter of OPA's 20%-default punt (r = +0.52 with default share), but the OPA gradient survives controlling for it (partial r = −0.46): OPA's genuinely-assessed splits in her base carry high land shares; LYCD's market-price method disagrees. Neither is ground truth; present both. |
| 2 | LYCD's flat 20% land share | ROBUST (relative claim) / WEAKENED (absolute) | (a) Band test 15–30%: all-SFR correlation stays flat (|r| ≤ 0.07 everywhere); owner-occ gradient deepens with share (−0.04 → −0.15) but stronghold homeowners stay majority-winners at every point (60–86%). Market-value-cap ambiguity immaterial (bounds nearly identical). (b) External: FHFA puts Philadelphia County SF land share at 25–29% (2012–22) — 20% is a modest underestimate; tract-level shares run 0.14–0.41, correlated +0.74 with value ([FHFA WP 19-01 data](https://www.fhfa.gov/research/papers/wp1901)). (c) FHFA-structured variant (tract share × taxable value): nearly all SFR citywide wins (96.6%), her strongholds do *better* than average (r = +0.22) — burden shifts to vacant land and Center City. First-pass version of this variant had a bug (applied shares to gross market value, silently deleting the homestead deduction); corrected version reported here. |
| 3 | Lot-area chain (DOR → LYCD) | VERIFIED | 90.4% PIN-level DOR coverage; $/sqft tails sane (p50 $57, p99 $516, one parcel >$10k). Missing-area KNN imputation concentrates *outside* her base (2.6% of stronghold parcels vs 11.8% elsewhere) — cannot be driving her base's result. |
| 4 | Levy scope (city+school 1.3998%) | ANALYTIC | Win rates and % changes are scope-invariant (uniform scaling); dollar magnitudes scale ×≈0.45 if the school share can't participate. The school district's share requires the same state enabling act — flag when quoting $ figures. |
| 5 | 4:1 ratio choice | ROBUST (gradient documented) | Owner-occ stronghold correlation: +0.02 (2:1) → −0.06 (3:1) → −0.11 (4:1); win rates 86% → 80% → 76%. Milder ratios are strictly safer for her base. Directly useful for the TJ conversation: if his model used a steeper ratio than 4:1, his worse result is partly explained. |
| 6 | Revenue neutrality vs collections | ASSUMPTION | Model equates billed, not collected; ~5% delinquency gap concentrates in low-income (winning) areas, so collected-revenue neutrality would require slightly higher millages. Second-order. |
| 7 | Exemption/abatement mechanics | VERIFIED (one distributional flag) | Homestead is embedded in `taxable_building`; abated parcels use `exempt_building` (fallback `market_value − taxable_land`). Correctly implemented. Flag: because homestead relief rides on the building side, the reform *dilutes* it — its value falls from ≈ $1,120/yr (80K × 13.998 mills) to ≈ $473/yr (80K × 5.91 mills). This is inside the reported win rates, but it is a real feature of split-rate worth stating openly. |
| 8 | Current-tax validation | VERIFIED (carried) | City-levy cross-check gap +5% ≈ normal delinquency (documented in CLAUDE.md/explainers); all four exports re-executed to byte-identical CSVs. |
| 9 | SFR parcel = homeowner voter | WEAKENED | 68.5% of SFR is owner-occupied (mailing-address proxy; 12-case spot-check looks clean — genuine absentee addresses). Stronghold investor share 33.5% vs 31.5% city. Owner-occupied-only: r = −0.106, stronghold 71.2% vs citywide 75.3%. The honest voter-level number is mildly negative, still >70% winners. |
| 10 | Renters in her coalition | VERIFIED (proxy) + ASSUMPTION (incidence) | Her strongholds are *not* renter-heavier than the city (rental-ish parcel mix 29.6% vs 31.4%, r = −0.03). The claim that land tax isn't passed through to rents is standard theory but untestable here; flag whenever renters are invoked as beneficiaries. |
| 11 | Magnitudes / loss aversion | VERIFIED (favorable) | Pre-abatement, owner-occupied stronghold: median winner −$203/yr; losers 29% shallow (median $130, p90 $502, p99 $2,191) vs rest-of-city losers (median $323, p90 $3,283, p99 $9,993). Post-abatement: stronghold median still a win (−$87); losers 41% but still shallow (median $169, p90 $536). No big-loss tail in her base in either scenario. |
| 12 | Multi-parcel owners | VERIFIED (favorable) | Only 2.5% of stronghold owner-occupants also receive bills for a losing investment parcel, *below* the 4.5% citywide rate. |
| 13 | Stronghold construct | ROBUST | Stable across 4 definitions (top-quartile share, ≥50% share, top-decile, top-quartile raw votes: 76–83%), parcel weighting, small-n filters, and turnout weighting (77.1% vs 75.4% citywide). |
| 14 | 2023 primary vintage | ASSUMPTION (corroborated) | General-election base measure agrees (stronghold median 82.2% vs citywide 82.3%); primary and general shares correlate r = 0.63. Her 2027 coalition is unknowable; flag. |
| 15 | "Northeast" / District 9 conflation | VERIFIED (reconciled) | D9's weakness is Olney/Lawncrest (wards 49: 60.3%, 17: 64.6%, 42: 65.4%), not her base: ward 50 (West Oak Lane, 71% Parker share) wins at 85.0%, ward 10 at 80.9%. Earlier session language lumping D9 into "the Northeast" conflated her home base with the genuinely weaker area; use D6/D10 + Olney-area wards when discussing TJ's Northeast concern. |
| 16 | Who the in-base losers are | VERIFIED (favorable, with flags) | Top-50 dollar losers inside stronghold precincts: 38 vacant land + 2 improved-vacant (the policy target), 5 industrial, 3 commercial, 2 abated. Politically loud homeowner losses are absent; industrial/commercial single-parcel increases up to ≈$0.5–1.0M are named organized-opposition risks. |
| 17 | Legal gate | ASSUMPTION (outermost) | All palatability claims are conditional on PA state enabling legislation that no sitting legislator currently sponsors (see the political briefs). |
| 18 | Bottom-line reconciliation | — | See "Bottom line" above and "What to tell TJ" below. |

## What to tell TJ (supersedes earlier session formulations)

1. **The Northeast effect is real but concentrated and modest.** Under LYCD the genuinely weaker area is the Far Northeast plus Olney/Lawncrest (win rates 60–73%), not a monolithic "Northeast," and not the Mayor's own base wards (80–85%). Under the FHFA market-calibrated structure, even the Far Northeast is majority-winner.
2. **The Mayor's personal political exposure is limited, stated carefully:** most of her base's *homeowners* win under every structure tested; their losses, where they occur, are shallow; and her base's large losers are vacant-land holders. The honest caveats: owner-occupied homes in her base trail the citywide win rate by ~4pp (LYCD 4:1); the city's own OPA splits would say her base is somewhat exposed; the claim does not extend to commercial parcels in her coalition.
3. **Design levers matter in her favor:** a milder ratio (2:1) eliminates even the ~4pp owner-occupied gap; and if TJ's model used a steeper effective ratio or OPA's raw splits, both differences push toward his more pessimistic conclusion.
4. **Two structural honesty points for any public claim:** the reform as modeled roughly halves the dollar value of the Homestead Exemption (rides on the building millage), and all dollar figures assume the school-district share participates — city-only action scales them by ≈0.45.

## Corrections to earlier in-session claims

- "Parker's stronghold ≈ citywide, full stop" → holds for all-SFR; **owner-occupied-only shows a real ~4pp deficit** (r = −0.106). Earlier statements lacked this cut.
- The first FHFA-structured computation reported in-session (stronghold 43.8% owner-occ win rate) was **wrong** — it applied land shares to gross market value, deleting the homestead deduction from the reform side. Corrected variant: ~100% median win rates, favorable r = +0.22.
- "District 9 is the Near Northeast and the weakest district" — true as stated but conflated with her base; ward-level decomposition (link 15) is the correct picture.
- Project memory's OPA millages (28.80/7.20) were stale; current model: 29.08/7.27 (fixed in memory 2026-07-18).

## Verification trail

All computations in this report were produced from: the four verified exports, `cities/philadelphia/data/parcels.gpq`, `opa_mailing.parquet` (owner-occupancy proxy), the 2023 City Commissioners returns + OpenDataPhilly division boundaries (13-01 fix applied), and the FHFA June-2024 land-price dataset (tract cross-section). The two compute batteries (land-share band, ratio band) are closed-form re-solves reproducing the notebook's `model_split_rate_tax` math; the 4:1/20% cell of the grid exactly reproduces the shipped headline numbers (r = 0.007, stronghold 80.4%, citywide 82.3%), anchoring the grid to the audited baseline.
