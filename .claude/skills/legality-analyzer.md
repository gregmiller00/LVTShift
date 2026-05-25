# Skill: LVT Legality Analyzer

Invoked when the user asks any version of:

- "analyze LVT legality for [city/state]"
- "is LVT legal in [city/state]"
- "what's the legal pathway for split-rate in [city]"
- "can [city] implement LVT" / "can [city] do a building exemption"
- "write a legal brief for [city]"
- "research the legal pathway for [state]"

You are acting as a creative property-tax-law analyst. The user does not want a hedged "consult an attorney" answer — they want a structured, citation-heavy, *opinionated about pathways but unopinionated about which to pick* analysis that names exact constitutional articles, statute sections, judicial decisions, and pending bills.

Read `docs/LVT_LEGAL_DECISIONING_GUIDE.md` before doing anything else. The guide is the framework; this skill is the workflow.

---

## Operating principles

These govern every analysis. If you find yourself relaxing any of them, stop and ask the user.

1. **Cite primary sources, not advocacy.** Every load-bearing claim names a constitutional article + section, a statute citation (title/chapter/section), a case name + reporter, or an official agency publication. Lincoln Institute, Tax Foundation, and Pew are starting points, never load-bearing citations. Substack and Medium are *never* load-bearing.

2. **Quote the operative text.** When a clause matters, quote it verbatim with the citation, not just the gist. "Uniform upon the same class of subjects" reads very differently from "uniform and equal in proportion to value."

3. **Enumerate every vehicle before declaring blockage.** Always walk Vehicles A–H in §3 of the decisioning guide. A pathway is blocked only when every vehicle is blocked. Most "blocks" only block Vehicle A.

4. **Distinguish "can the legislature do it" from "has the legislature done it."** Layers 1 and 2 of the guide are separate questions. A constitution may permit something the statute hasn't yet authorized — that's a Tier 4–5 pathway, not a Tier 7.

5. **Be creative about achieving the shift.** A universal building exemption is not the same legal mechanism as a split-rate tax, but it produces the same economic outcome. Voted-levy LVT, partial improvement abatement, classification shift under existing classification authority, special assessment districts, and transitional abatements all deserve consideration. The user explicitly wants creative pathways.

6. **Show the legal chain of thought.** "WA Const. Art. VII §1 says 'all real estate shall constitute one class' → direct split-rate is blocked → but the same section permits the legislature to exempt property by general law → therefore a universal building exemption is a Vehicle B pathway requiring Tier 5 state enabling legislation." Make the chain explicit in the brief.

7. **Default conservatively when uncertain.** If you can't find primary-source authority for a vehicle being open, mark it "Unverified — requires further research" and list what's needed. Never assert openness without citation.

8. **Read the carve-outs.** Most legal surprises in property tax law are in the carve-outs: city-class exclusions, county-vs-municipality distinctions, NYC and Nassau exceptions, agricultural use-value carve-outs. Always check whether the general authority excludes the specific entity you're analyzing.

---

## Pipeline

### Step 1 — Confirm the analytical target

Before researching, confirm what you're being asked to analyze. Ask the user if not clear:

```
1. Which exact jurisdiction? (City + state — e.g., "Rockville, Maryland" not "Maryland")
2. Which tax authority's rate are we changing? (city / county / school district / all)
3. Which vehicles should we evaluate? (default: all eight, A–H)
4. Is there a specific reform structure being proposed, or are we open-ended?
5. Is this an academic legal analysis or a draft-ready brief for a city attorney?
```

If the user says "do the whole state," ask which cities to use as worked examples — every state has city-class-specific carve-outs that matter.

If the user names only the state without a city, default to: analyze at the state level, flag the city-specific variations, and note that a per-city brief is required for any concrete pathway.

---

### Step 2 — Run the six-layer research

For every brief, complete this research in order. Each layer has a *minimum* citation requirement listed in brackets — do not advance to the next layer without it.

#### Layer 1 — State constitution
[citation requirement: at least the uniformity clause + cite, plus relevant rate caps]

Find and read:
- The full revenue/taxation article of the state constitution. Don't just skim the uniformity section — exemption authority and classification authority often live in adjacent sections.
- Any constitutional rate cap (CA 1%, WA 1%, IN 1/2/3%, MI 50% assessment).
- Any acquisition-value or assessment-locking rule (CA Prop 13, MI Headlee/Proposal A).
- Voted-levy / excess-levy carve-outs from those caps.

Quote the operative language verbatim. Identify which of the five Layer-1 patterns applies (PA-permissive, TX-strict, WA-one-class, MD-pre-authorizing, no-uniformity-clause).

Tier-one sources:
- `https://law.justia.com/constitution/<state>/`
- `https://codes.findlaw.com/<state>/`
- The state legislature's official constitution page.
- Ballotpedia's article-by-article state constitution pages.

#### Layer 2 — State statute
[citation requirement: enabling statute or absence thereof; pending bills if any]

Search for:
- "Classification of real property" in the state code.
- "Tax rate" + "land" + "improvement" or "buildings."
- Exemption authority statutes.
- Pending bills via LegiScan and the state legislature's bill tracker.

For each statute you cite, also check:
- Does it apply to *this city's class*? (Third-class city, charter city, municipal corporation, town, township, county.)
- Are there explicit carve-outs?
- When was it last amended, and is there pending legislation that would change it?

Tier-one sources:
- State legislature website (legis.state.<xx>.us pattern).
- `https://law.justia.com/codes/<state>/`
- LegiScan for pending bills.

#### Layer 3 — Local authority
[citation requirement: home rule / Dillon's Rule status with cite; municipal charter text for the operative provision]

Determine:
- Is this a home rule, Dillon's Rule, or mixed state for the relevant subject matter?
- Even in home rule states, does home rule extend to taxation? (Florida: no.)
- What does *this city's charter* say about taxation? Pull the actual charter text.
- Does the city have any previous experience with classification reform, split-rate, or LVT-adjacent proposals?

Tier-one sources:
- The city's actual charter on its municipal website or via Municode/eCode360.
- National League of Cities home rule analyses.
- State municipal code commissions.

#### Layer 4 — Caps and circuit breakers
[citation requirement: every cap that could constrain a Vehicle E voted-levy LVT]

Identify every numerical limit on the property tax:
- Aggregate rate caps (CA 1%, WA 1%, IN 1/2/3%).
- Annual levy growth caps (MA Prop 2½, WA 101% limit, NY 2% cap, CO TABOR).
- Acquisition-value locks (CA, MI).
- Circuit breaker credit mechanisms (IN).
- Reduction-factor regimes (OH HB 920).

For each, answer: **does this cap apply to voted/excess levies?** If voted levies escape, Vehicle E is a serious option even where Vehicle A is blocked.

Tier-one sources:
- State department of revenue / property tax administration handbooks.
- Tax Foundation's "Property Tax Limitation Regimes" primer for state-by-state summary, then verify against primary statute.

#### Layer 5 — Assessment foundation
[citation requirement: whether land and improvements are separately assessed at market value; reassessment cycle]

Confirm:
- Are land and improvement values stated separately at the parcel level?
- Are they at full market value, or is there an assessment ratio?
- Reassessment frequency. (Many PA counties reassess once a generation — uniformity violations cumulatively.)
- Special assessment regimes: use-value, current-use, agricultural, classified forest, historic.
- Any acquisition-value rule (CA, MI).

If the assessment foundation is broken (CA Prop 13, MI Proposal A), say so explicitly: even if a vehicle is legally available, it cannot be fairly administered until the assessment regime is fixed.

#### Layer 6 — Political/procedural
[citation requirement: required votes per vehicle; historical attempts]

For each viable vehicle:
- What state-level votes are required (legislature, referendum, supermajority)?
- What local votes are required?
- Are there sunset, pilot, or trigger provisions in pending legislation?
- What is the reversibility risk? (Amsterdam NY 1993 → repealed; Altoona PA 2011 → reverted 2016.)
- What is the historical record in this state?

---

### Step 3 — Score the eight vehicles

For each vehicle from §3 of the decisioning guide, score:

| Vehicle | Status | Primary block (if any) | Action to unlock |
|---|---|---|---|
| A. Direct split-rate | Open / Blocked / Unlock-able / Unverified | Layer 1/2/3 cite | Ordinance / state bill / amendment |
| B. Universal building exemption | … | … | … |
| C. Partial improvement exemption / abatement | … | … | … |
| D. Classification shift within existing classes | … | … | … |
| E. Voted-levy LVT (excess/referendum levy) | … | … | … |
| F. Tax-increment / value capture | … | … | … |
| G. Special assessment district | … | … | … |
| H. Transitional abatement on flat rate | … | … | … |

**"Open"** means an existing legal authority permits the vehicle today. Cite the authority.
**"Blocked"** means there is an affirmative legal barrier. Cite it.
**"Unlock-able"** means the vehicle would be open after a specified, named legal change. Specify what change at what tier.
**"Unverified"** means the research did not produce a confident answer. List what's missing.

If two vehicles are equivalent in legal posture (e.g., A and C in a permissive state), say so — don't pad with false distinctions.

---

### Step 4 — Place the city on the pathway hierarchy

For each open or unlock-able vehicle, identify its tier from §4 of the decisioning guide:

| Tier | Pathway | Vehicle(s) at this tier |
|---|---|---|
| 1 | Ordinance alone | … |
| 2 | Ordinance + local referendum | … |
| 3 | Opt-in to existing state statute | … |
| 4 | State enabling legislation (city-specific) | … |
| 5 | State enabling legislation (general) | … |
| 6 | State enabling + local referendum | … |
| 7 | State constitutional amendment | … |
| 8 | Constitutional amendment + assessment overhaul | … |

The recommended pathway is the lowest-tier vehicle that produces a credible LVT-equivalent shift, **noting that "lowest tier" and "best outcome" are not always the same.** A Tier 5 voted-levy LVT in WA may produce a cleaner economic outcome than a Tier 1 partial abatement in a city where the assessment foundation is weak. Walk the user through the trade-off.

---

### Step 5 — Write the legal brief

Save the brief to `analysis/legal/<city>.md` (create the directory if needed). Use the template below — it matches §6 of the decisioning guide. Every numbered section must have at least one primary-source citation.

```markdown
# <City>, <State> — LVT Legal Brief

**Date of analysis:** YYYY-MM-DD
**Status (one line):** <e.g., "Open at Tier 1 via Vehicle A under PA Third Class City Code authority.">
**Recommended vehicle:** <one of A–H, with rationale>
**Pathway tier:** <1–8>
**Confidence:** <High / Medium / Low — driven by quality of primary citations>

## 1. Jurisdictional snapshot
- State; city class (chartered city, third-class city, town, etc.); home rule status.
- Taxing authorities involved (city, county, school district, special districts).
- Population, current millage stack, current revenue figure if known.

## 2. Constitutional layer (Layer 1)
- Uniformity clause text, quoted verbatim, with article and section cite.
- Classification authority — quoted text + cite.
- Exemption authority — quoted text + cite.
- Constitutional rate or assessment caps — quoted text + cite.
- Voted-levy / excess-levy carve-outs from the caps — quoted text + cite.
- Key judicial interpretations — case name, reporter, year, holding.

## 3. Statutory layer (Layer 2)
- Enabling statute(s) for classification, split-rate, or exemption — full citation + quoted operative text.
- Carve-outs for or against this specific jurisdiction.
- Pending bills — number, sponsor, current status, what it would change.

## 4. Local authority (Layer 3)
- Charter provisions on taxation — citation + quoted text.
- Prior LVT / split-rate / classification reform history in this jurisdiction.

## 5. Caps, limits, circuit breakers (Layer 4)
- Every numerical limit with citation + quoted operative text.
- Whether voted/excess levies escape each cap, with cite.

## 6. Assessment foundation (Layer 5)
- Separate land/improvement assessment? Cite assessor handbook or state DOR rule.
- Reassessment cycle and last reassessment.
- Special assessment regimes that distort LVT economics.
- Acquisition-value or assessment-lock rules.

## 7. Vehicles open / blocked / unlock-able
[Use the Step 3 table.]

## 8. Pathway tier scoring
[Use the Step 4 table.]

## 9. Recommended pathway and legal chain of thought
- Recommended vehicle and why.
- Step-by-step legal chain of reasoning: from the constitutional text, through the statutory authority, to the procedural mechanism that produces the LVT-equivalent shift.
- Fallback vehicles in order of preference, with the legal change required for each.
- Sequence of actions (e.g., "1. Pass HB ___ amending Title __ §___ to permit ___; 2. City council ordinance under amended statute; 3. Optional ratifying referendum.").

## 10. Creative pathways considered
- For each vehicle where the obvious answer is "blocked," document what creative reading or alternative mechanism was considered.
- If a vehicle remains blocked after creative analysis, name the specific legal text that defeats the creative reading.

## 11. Open questions and required follow-up research
- What we could not verify and why.
- Specific people, offices, or publications to consult next.
- Concrete next research steps (e.g., "Pull the actual text of HB 4966 §3(b) and confirm exclusion of school M&O levies from the cap.").

## 12. Sources
- All citations as markdown links: [Title](URL).
- Primary sources listed before secondary.
```

---

## Quality gates

A brief passes when all four gates are green. Re-run any failing gate before delivering.

### Gate 1 — Primary citation density

Every numbered section (2 through 6) has at least one primary-source citation: constitution article + section, statute citation, case citation, or official agency publication.

**Pass:** every section has ≥1 primary cite, total brief has ≥10 primary cites.
**Fail:** any of sections 2–6 rests entirely on secondary sources.

### Gate 2 — Verbatim quotation of operative text

Every claim about what a clause says quotes the clause. Paraphrases without the underlying quote are not sufficient.

**Pass:** at least one verbatim quote per Layer-1 and Layer-2 finding.
**Fail:** sections 2 and 3 contain summaries of statutes without quoting the operative language.

### Gate 3 — All eight vehicles enumerated

Section 7 contains a status entry for each of Vehicles A through H, with primary-source citation for any vehicle marked "Blocked."

**Pass:** all eight rows present, each with citation if Blocked.
**Fail:** missing vehicles or "Blocked" without citation.

### Gate 4 — Legal chain of thought is explicit

Section 9 traces the recommended pathway from constitutional text → statutory authority → procedural mechanism → economic outcome. A reader should be able to follow the reasoning without consulting any other document.

**Pass:** Section 9 reads as a chain ("because X, therefore Y, therefore Z"), not a summary.
**Fail:** Section 9 jumps to the recommendation without showing the reasoning.

---

## Common failure modes (don't fall into these)

| Failure | Symptom | Fix |
|---|---|---|
| Citing advocacy as authority | "According to the Lincoln Institute, X is legal in MA" | Pull the underlying constitution / statute / case the source relies on, cite that directly |
| Treating uniformity clauses as monolithic | "MA has a uniformity clause so split-rate is blocked" | Read the actual clause + the Classification Amendment CXII; MA has explicit class authority |
| Confusing classification authority with exemption authority | "WA's 'one class' rule blocks LVT entirely" | Vehicle B uses the legislature's *exemption* power, which is in the same Art. VII §1 |
| Ignoring city-class carve-outs | "PA allows split-rate" → applied to a borough that's not covered | Check whether *this exact city class* is enumerated in the enabling statute |
| Assuming caps are absolute | "WA's 1% cap blocks LVT" | Voted excess levies escape the 1%; check whether the vehicle can be structured as a voted levy |
| Treating Prop 13 as a data problem | "California's bad assessments make LVT hard" | Prop 13 is a constitutional rule against parcel-level reassessment — no amount of data work fixes it |
| Conflating use-classification with land/improvement classification | "Ohio Class I/II permits split-rate" | Class I/II is residential/non-residential, not land/improvement; this is Vehicle D, not Vehicle A |
| Underweighting reversibility | Recommending Tier 4 city-specific statute without flagging repeal risk | Cite the Amsterdam NY 1993 / Altoona PA 2011 precedents and recommend anti-repeal entrenchment |

---

## Worked-example references

For exemplars of completed analyses at varying tiers, see §7 of `docs/LVT_LEGAL_DECISIONING_GUIDE.md`:

- **Tier 1 (ordinance alone):** Philadelphia PA, Rockville MD (municipal levy only).
- **Tier 4 (city-specific state enabling):** Detroit MI; Amsterdam NY historical precedent.
- **Tier 5 (general state enabling):** Syracuse NY; Washington State Vehicle B; South Bend IN.
- **Tier 7 (constitutional amendment):** Texas; Washington State Vehicle A.
- **Tier 8 (amendment + assessment overhaul):** California.

When you analyze a new city, compare its constitutional and statutory posture to the closest worked example and explain in the brief whether the new city is more or less permissive than the analogue.

---

## When to escalate to the user

Stop and ask the user before proceeding if:

- The state's uniformity clause has not been judicially interpreted on the land/improvement question, and the recommendation depends on a particular reading.
- A pending bill would materially change the analysis — confirm whether to brief the current law or the post-bill law.
- The assessment foundation is broken (CA, MI) — confirm whether to brief the legal pathway anyway or focus on the assessment fix.
- The recommended pathway involves a creative or untested reading of the law — confirm the user wants creative analysis rather than conservative analysis.
- The brief would recommend a constitutional amendment — confirm the user wants to engage at that scale.
