# Skill: Export and Visualize

## Goal
Save the standardized export CSV and produce the standard visualization suite. At the end of this skill, `analysis/data/<city>.csv` exists and 5 standard charts have been produced in the notebook.

---

## Part 1 — Export

### The export cell

The export cell goes at the end of Section 4 (Tax Modeling), after `model_split_rate_tax()` has run and after the Census join. Place it as a standalone cell with this comment: `# Export standardized CSV — do not remove or move above Census join`.

Call `save_standard_export()` from `lvt_utils`. Required arguments:

| Argument | What to pass |
|---|---|
| `df` | Final DataFrame after Census join |
| `city` | Lowercase slug matching the notebook's folder name |
| `output_path` | `'../../analysis/data/<city>.csv'` |
| `model_type` | Encoded string: `"split_rate:4.0"`, `"abatement:50pct"`, etc. |
| `land_millage` | Return value from `model_split_rate_tax()` |
| `improvement_millage` | Return value from `model_split_rate_tax()` |

Optional arguments (all have defaults, but set explicitly for clarity):
- `property_category_col` — if not 'PROPERTY_CATEGORY'
- `exempt_flag_col` — column with boolean/binary fully-exempt flag
- `new_tax_col` — if the city renames it (e.g., St. Paul uses `new_tax_tc`)

The function prints a confirmation line and warns about non-standard categories — both are expected and normal.

### Model type encoding

Format: `<kind>:<param>[,<kind>:<param>...]`

- `split_rate:4.0` — 4:1 land-to-improvement ratio
- `split_rate:2.0` — 2:1 ratio
- `abatement:100pct` — full building exemption
- `abatement:50pct` — 50% building abatement
- `exemption:50000` — $50,000 dollar base exemption on improvements
- Stacked: `split_rate:4.0,exemption:50000`

---

## Part 2 — Standard Visualization Suite

Apply the style before any plotting: `from lvt.style import apply_lvt_style; apply_lvt_style()`

### Chart 1 — Property category impact (bar chart)

Use `create_property_category_chart()` or the Spokane-style multi-panel chart from `viz.py`. Shows median tax change % by property category. Use `CATEGORY_COLORS` from `lvt.style` for consistent colors across cities.

Exclude fully exempt parcels. Sort by parcel count descending. Include a reference line at 0%.

### Chart 2 — Income quintile analysis

Use `create_quintile_summary()` + `plot_quintile_analysis()` from `viz.py`. Groups block groups into 5 income quintiles and shows median tax change % for each.

Run twice: once including all taxable parcels, once excluding Vacant Land. Both panels are informative — vacant land exclusion shows the residential equity story.

### Chart 3 — Minority quintile analysis

Same functions, `quintile_col='minority_pct'`. This shows whether LVT impacts correlate with racial composition.

### Chart 4 — Scatter: parcel-level income vs. tax change

Use `create_scatter_plot()`. X-axis: block group median income. Y-axis: parcel tax change %. Show trend line. Exclude parcels with `current_tax == 0`.

### Chart 5 — Threshold chart

Use `create_threshold_change_chart()` or `plot_upside_down_quintile_bars()`. Shows what % of parcels in each quintile see increase >10% vs. decrease >10%. Useful for policy communication ("most low-income homeowners see modest decreases").

### Optional additional charts

- Scatter: minority % vs. tax change %
- Map: choropleth of tax change by parcel
- Multi-scenario comparison (2:1, 4:1, 10:1) — useful for cities where multiple ratios are analyzed

---

## Notebook section for visualizations

All charts go in Section 7: Equity & Visualization. Keep Section 6 for analysis summaries (category summary table, vacant land analysis, parking analysis).

**Verification criteria for this skill:**
- [ ] `analysis/data/<city>.csv` exists with 16 columns
- [ ] `save_standard_export()` printed a `✓` confirmation line
- [ ] 5 standard charts are in the notebook (income quintile, minority quintile, scatter, threshold, category bar)
- [ ] Charts use colors from `lvt.style.CATEGORY_COLORS`
- [ ] `apply_lvt_style()` is called at the top of the notebook
