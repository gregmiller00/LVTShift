# Audit: Philadelphia LVT analyses and the "Mayor's base is safe" claim

**Date:** 2026-07-18
**Scope:** End-to-end audit of the Philadelphia model exports, the 2023 election-data pipeline, the mayor-exposure map/scatter scripts (`scripts/map_philadelphia_mayor_exposure.py`, `scripts/scatter_philadelphia_mayor_exposure.py`), and the two subagent-authored political briefs (`analysis/political/philadelphia_lycd{,_post_abatement}.md`).
**Claim under audit:** Mayor Parker's electoral base (top-quartile 2023-primary vote-share precincts) is not disproportionately exposed to LVT reform losses under the LYCD models.

## Verdict

**The headline claim survives the audit, with one required qualification.** Every headline number reproduces independently; the two bugs found are quantified below and neither moves any reported figure at the displayed precision. The required qualification: the "base is safe" result is established for **homeowners (SFR, and residential broadly)** — on an **all-taxable-parcel** basis her stronghold *is* mildly more exposed than the city (r = −0.166, 67% vs 69% parcel-weighted win rate), consistent with commercial-corridor precincts inside her coalition. Messaging built on this analysis should say "her homeowner base," not "her base," or carry the commercial caveat.

## Layer A — Model exports

- **Reproducibility: PASS.** All four notebooks re-executed headlessly (0 errors) and regenerated CSVs are **byte-identical** to the versions on disk. No stale-export drift.
- **Revenue neutrality: PASS.** All four exports: current vs new revenue gap 0.000%; land/improvement millage ratio exactly 4.000.
- **Documented values: PASS** with one stale-memory note: OPA pre-abatement millages are 29.08/7.27 (project memory said 28.80/7.20 — a value from before the abated-parcel building-value imputation change; the memory note, not the model, is stale). LYCD 23.64/5.91 and both post-abatement pairs match documentation exactly.
- **Known join traps: PASS.** No index-based joins in the new scripts; leading-zero stripping produces zero true collisions.
- **Finding A-1 (immaterial): duplicate parcels in source.** 4 parcel numbers appear 2–4× each (14 rows) in both `parcels.gpq` and every export — genuine OPA source duplicates, not a join artifact. The m:m merge in the exposure scripts inflates the joined table by 38 rows out of ~580K (0.007%). No visible effect at reported precision.

## Layer B — Election data (2023 primary returns + ward-division boundaries)

- **External anchor: PASS (exact).** Computed citywide Parker share = 32.6%, matching the official 2023 Democratic primary result.
- **Denominator: PASS.** The `MAYOR`+`DEM` column filter catches exactly the 9 Democratic candidates + Write-in; no totals column contamination. (Note: any *count*-level sum over the raw sheet must exclude the `COUNTY TOTALS` row — shares are unaffected because it scales numerator and denominator equally.)
- **Geographic spot-checks: PASS.** Ward 66 → Far Northeast, 27 → University City, 39 → South Philly, 50 → West Oak Lane (Parker's home ward) — all centroids land where they should.
- **Returns table structure: PASS.** 1,704 unique non-null precinct rows (1,703 precincts + `COUNTY TOTALS`); the ~3,400 extra sheet rows are empty padding; no duplicate precinct blocks.
- **Finding B-1 (real bug, immaterial): precinct 13-01 mislabeled.** Boundary polygon OBJECTID 533 has internally inconsistent source fields (`DIVISION_NUM='1301'` but `SHORT_DIV_NUM='13'`). The scripts' name construction trusts `SHORT_DIV_NUM`, so the 13-01 polygon is labeled as a duplicate "13-13": the real 13-01 returns row never joins, and 13-01's parcels are pooled into 13-13 with 13-13's vote share. **Impact quantified: rebuilding the entire pipeline with the corrected construction (`DIVISION_NUM[:2] + '-' + DIVISION_NUM[2:]`) leaves every headline number unchanged to 3 decimals** (LYCD r = 0.007, OPA r = −0.332, stronghold medians 80.4%/66.9%). Recommended fix for the scripts regardless.

## Layer C — Spatial joins

- **Geographic-CRS centroid warning: PASS.** Recomputing all parcel centroids in EPSG:2272 (projected) changes no precinct assignment outcome at reported precision — identical r values and medians. The warning is cosmetic for this use (point-in-polygon on small parcels); fixing it is good hygiene.
- **Dropped parcels: PASS.** 3 of ~580K parcels fall outside all precinct polygons (boundary slivers); no geographic clustering of consequence.
- **Small-precinct sensitivity: PASS.** Stronghold median SFR win rate is 80.4% / 80.4% / 80.3% at minimum-n thresholds of 1 / 10 / 25. The map (no filter) and scatter (n≥10) are consistent.

## Layer D — Validity of the inference

- **D-1 Scope sensitivity (the required qualification).** LYCD pre-abatement, stronghold vs citywide:
  | Scope | r (share vs win rate) | Stronghold win rate (parcel-wtd) | Citywide (parcel-wtd) |
  |---|---|---|---|
  | SFR only | +0.007 (n.s.) | 76.6% | 76.6% |
  | All residential + mixed | +0.014 (n.s.) | 78.1% | 78.0% |
  | All taxable | **−0.166 (p<0.001)** | 67.1% | 69.1% |
  The homeowner claim is rock-solid; the all-parcel measure shows mild negative exposure (commercial corridors in her coalition). Two-thirds of all taxable parcels in her stronghold still win.
- **D-2 Stronghold definition: robust.** Top-quartile share (80.4%), share ≥50% (80.1%), top-decile share (82.7%), top-quartile raw votes (75.8%) — all comfortably above 50%, all near the citywide 82.3% precinct median.
- **D-3 Weighting: robust.** Parcel-weighted stronghold SFR win rate (76.6%) exactly matches citywide (76.6%).
- **D-4 OPA-vs-LYCD divergence — adjudicated.** Why OPA says her base is exposed (r = −0.33) and LYCD says it isn't (r = 0.01):
  1. Parker's strongholds are precisely where OPA defaults land ratios: correlation between her precinct vote share and the share of SFR parcels at OPA's 0.200 default is **r = +0.52**. Her Northwest base is the epicenter of OPA's assessment punt.
  2. **The "LYCD flattens geography" concern is rejected**: cross-precinct variation in median land ratio is *higher* under LYCD (SD 0.076 vs 0.063), and win-rate dispersion is comparable (18.2pp vs 20.3pp). The flat LYCD correlation is not a mechanical artifact of the 20%-flat-share construction compressing variation.
  3. However, the OPA gradient is **not purely the default-LR artifact**: controlling for the precinct default share, the negative OPA gradient persists and strengthens (partial r = −0.46). Where OPA assessors *did* assign real splits in her base neighborhoods, they assigned relatively high land shares; LYCD's market-price-times-lot-area method disagrees with those splits.
  4. **Honest bottom line:** the sign of the Mayor's homeowner-base exposure depends on whose land-share estimates you believe — OPA's assessor-assigned parcel splits (45% defaulted citywide, most heavily in her base) or LYCD's zone-price-based construct. LYCD has the more principled market basis and is not artifactually flat; but the OPA result cannot be dismissed as *only* a data artifact. Any presentation should show both and explain the divergence rather than assert one as truth.

## Layer E — Subagent-authored briefs

- **Quantitative reproduction: PASS (exact).** All 10 district-level %SFR-decreasing values in the LYCD pre-abatement brief reproduce to 0.1pp; all 10 districts confirmed SFR-majority-winning. Parker's correlations reproduce (brief +0.01/−0.16 vs audit +0.007/−0.166; post-abatement −0.021/−0.147 confirmed via shipped scripts). Base-coalition SFR win rate 96.2% reproduces exactly.
- **Finding E-1 (framing risk): "base-coalition SFR win rate" definition.** The skill's metric is *the share of stronghold precincts that are majority-winning* (96.2%), not the share of stronghold homeowners who win (76.6%). Both are favorable, but the 96.2% figure invites misreading as the latter. Recommend the briefs (and any downstream messaging) state the definition inline.
- **Citation spot-check: PASS.** Legistar file 210191 confirms Parker among the seven co-sponsors of the LVT hearing resolution, adopted, hearing held 4/30/2021 — as both briefs claim. (Broader officials-table citations not re-verified individually; the two independently-researched briefs agree with each other on all shared claims, which is itself corroborating evidence.)

## Recommended follow-ups (not applied during audit)

1. Fix the precinct-name construction in `map_philadelphia_mayor_exposure.py` to use `DIVISION_NUM` alone (Finding B-1) and compute centroids in EPSG:2272 (silences the warning; both verified no-op on results).
2. De-duplicate the 4 doubled parcel numbers at export or join time (Finding A-1).
3. Add the scope qualification ("homeowner base," commercial caveat) wherever the result is quoted — including the two political briefs' precinct sections (Finding D-1).
4. Update the stale OPA millage figures in project memory (29.08/7.27).
5. When presenting to TJ/the Mayor's office, present the OPA-vs-LYCD divergence explicitly (D-4) — the LYCD result is the better-founded estimate, but the honest framing is "under the city's own assessment splits her base looks mildly exposed; under a market-based revaluation it does not," which is also an argument for pairing any LVT proposal with assessment reform.
