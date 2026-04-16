# Skill: Model the Tax

## Goal
Implement the city-specific tax logic to produce `current_tax` and `new_tax` columns on every parcel. At the end of this skill, you have a revenue-neutral split-rate (or abatement) model that has been validated against the official tax base.

---

## Step 1 — Identify the current tax system

Every city has a different tax system. Answer these questions before writing any model code:

**Millage / rate questions:**
- Is there a single millage rate for the whole city, or does it vary by property class, tax code area, or levy district?
- What is the base year for assessed values? (Affects what "current_tax" means — are you modeling based on assessed value or market value?)
- What government body levies the tax? City only? City + county + school district?
- Are you modeling the full property tax bill or just one jurisdiction's portion?

**Exemption questions:**
- Is there a homestead exemption? Dollar amount or percentage?
- Is there a senior/veteran exemption? Dollar amount, percentage, or full exemption?
- Does the assessor publish an "exemption amount" column? Or a flag column?
- Are fully exempt parcels included in the data, or already excluded?
- Which comes first — partial exemptions or full exemptions? (Answer: partial exemptions reduce improvement value first, then land; full exemptions zero everything.)

**Special situations by state/city type:**
- **Minnesota**: Uses Tax Capacity (class rates applied to EMV) rather than raw EMV. Split-rate model uses TaxCapacity_Land and TaxCapacity_Improvements split by the improvement ratio.
- **Cook County (IL)**: Assessed values are 1/3 of market value. Multiply all values by 3.0 before modeling.
- **Spokane / Seattle**: Per-levy structure — each levy has its own millage; model each levy separately then sum.
- **Pittsburgh**: `LOCALLAND` / `LOCALBUILDING` / `LOCALTOTAL` fields already have homestead adjustments applied.

---

## Step 2 — Implement current tax

Use `calculate_current_tax()` from `lvt_utils`. Key decisions:

**If millage is a single scalar:**
```
millage_rate = 22.48  # mills, per $1,000 of assessed value
```

**If millage varies by parcel (tax code area, class rate, etc.):**
```
# Add a column to df with the per-parcel millage before calling the function
df['millage_rate'] = df['tax_code_area'].map(levy_lookup)
```

**If there is a dollar exemption:**
Pass `exemption_col=` — the function applies it to improvements first, then land.

**If there is a flag for fully exempt parcels:**
Pass `exemption_flag_col=` — the function zeroes out both land and improvement values.

**Validate against the official tax base:**
After `calculate_current_tax()`, print `total_revenue = df['current_tax'].sum()`. Compare this to the official city budget figure. Acceptable tolerance: within 2%. Differences of 5%+ usually indicate a wrong millage rate, missing exemptions, or filtering the wrong parcels.

---

## Step 3 — Classify properties

Use `categorize_property_type()` or write city-specific mapping logic to create a `PROPERTY_CATEGORY` column using the standard taxonomy. Key rule: any parcel with $0 improvement value should be classified as 'Vacant Land' regardless of use code.

The standard categories are the typical ones, but city-specific categories are allowed (e.g., South Bend uses 'Single Family' instead of 'Single Family Residential'). Do not force non-standard categories to fit — the export function will warn but accept them.

---

## Step 4 — Choose the model type

**Split-rate tax (most common):**
Land is taxed at X times the improvement rate. The ratio is the key policy variable. Common ratios:
- 2:1 — mild shift
- 4:1 — moderate (most common in analysis)
- 6:1 — aggressive
- 10:1 — near full land value tax

Use `model_split_rate_tax()` with `land_improvement_ratio=X`.

**Building abatement (percentage):**
A percentage of building value is exempt. E.g., 50% abatement means only 50% of improvement value is taxed. A single millage applies to the remaining taxable value.

Encode as: `model_type = "abatement:50pct"` or `"abatement:100pct"`.

**Dollar base exemption:**
The first $X of improvement value is exempt. Equivalent to a building abatement but bounded by a dollar cap.

Encode as: `model_type = "exemption:50000"` (the dollar amount).

**Stacked models:**
Some analyses combine a split-rate with an exemption floor, e.g., `"split_rate:4.0,exemption:50000"`. Encode both in the model_type string, comma-separated.

---

## Step 5 — Run the model

For split-rate: call `model_split_rate_tax()`. It returns `(land_millage, improvement_millage, new_revenue, df_with_new_tax)`.

Revenue neutrality is maintained automatically. The returned `new_revenue` should equal `current_revenue` within 0.5%.

For abatement models: use `model_full_building_abatement()` or `model_stacking_improvement_exemption()`.

---

## Step 6 — Validate the model output

Print and inspect:
- `new_revenue` vs `current_revenue` — should be within 0.5%
- `df['tax_change'].describe()` — mean should be near 0 (revenue-neutral)
- `(df['tax_change'] > 0).mean()` — at a 4:1 ratio, typically 55–65% of parcels see an increase
- `df[df['PROPERTY_CATEGORY'] == 'Vacant Land']['tax_change_pct'].median()` — should be a large positive number (vacant land gets taxed more under LVT)
- `df[df['PROPERTY_CATEGORY'] == 'Single Family Residential']['tax_change_pct'].median()` — should be a small negative or positive number depending on city land/improvement mix

**Verification criteria for this skill:**
- [ ] `current_tax.sum()` within 2% of official city revenue figure
- [ ] `new_tax.sum()` within 0.5% of `current_tax.sum()`
- [ ] `PROPERTY_CATEGORY` column exists with no null values
- [ ] Vacant Land parcels show large positive `tax_change_pct`
- [ ] `taxable_land_value` and `taxable_improvement_value` columns exist (added by the model function)
