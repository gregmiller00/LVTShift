from pathlib import Path
from textwrap import dedent

import nbformat as nbf


NOTEBOOK_PATH = Path("examples/baltimore.ipynb")


def md(text: str):
    return nbf.v4.new_markdown_cell(dedent(text).strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(dedent(text).strip() + "\n")


nb = nbf.v4.new_notebook()
nb["cells"] = [
    md(
        """
        # Baltimore City Levy Policy Example

        This notebook rebuilds the Baltimore model using the step order from `LVT_MODELING_GUIDE.md` and packages the work into a cleaner, reproducible workflow. It loads parcel data from Baltimore City's `Realproperty_OB` ArcGIS layer, validates the current city levy, models multiple revenue-neutral split-rate scenarios, and produces the main property-category and equity visualizations used elsewhere in this repo.

        Policy assumptions used here because no narrower specification was provided:

        - Scope: **Baltimore city levy only**
        - Reform type: **split-rate land value tax**, with `2:1` as the primary scenario and `4:1`, `10:1`, and land-only as benchmarks
        - Current-law structure preserved unless noted otherwise: **yes**
        - Existing exemptions / abatements preserved: **yes**, to the extent they are already embedded in Baltimore's taxable base fields
        - Existing credits preserved: **not explicitly modeled**, because `CITY_TAX` in this dataset appears to represent the gross city levy before parcel-level credit amounts such as `CCREDAMT`
        """
    ),
    code(
        """
        import os
        import sys
        import time
        from pathlib import Path

        import geopandas as gpd
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import requests
        import seaborn as sns
        from dotenv import load_dotenv
        from shapely.geometry import Polygon

        REPO_ROOT = Path.cwd()
        if not (REPO_ROOT / "lvt_utils.py").exists():
            REPO_ROOT = REPO_ROOT.parent

        if str(REPO_ROOT) not in sys.path:
            sys.path.append(str(REPO_ROOT))

        load_dotenv(REPO_ROOT / ".env")

        from census_utils import get_census_data_with_boundaries, match_to_census_blockgroups
        from lvt_utils import (
            calculate_category_tax_summary,
            calculate_current_tax,
            model_split_rate_tax,
            print_category_tax_summary,
        )
        from policy_analysis import (
            analyze_parking_lots,
            analyze_vacant_land,
            print_parking_analysis_summary,
            print_vacant_land_summary,
        )
        from viz import calculate_block_group_summary

        sns.set_theme(style="whitegrid")
        pd.set_option("display.max_columns", 140)
        pd.set_option("display.max_rows", 200)
        """
    ),
    code(
        """
        data_dir = REPO_ROOT / "examples" / "data" / "baltimore"
        data_dir.mkdir(parents=True, exist_ok=True)

        parcel_query_url = "https://geodata.baltimorecity.gov/egis/rest/services/CityView/Realproperty_OB/FeatureServer/0/query"

        attrs_cache = data_dir / "baltimore_attrs_20260326.parquet"
        geometry_cache = data_dir / "baltimore_geometry_20260326.parquet"

        attr_fields = [
            "OBJECTID",
            "PIN",
            "CURRLAND",
            "CURRIMPR",
            "EXMPLAND",
            "EXMPIMPR",
            "BFCVLAND",
            "BFCVIMPR",
            "ARTAXBAS",
            "CITY_TAX",
            "CITYCRED",
            "CCREDAMT",
            "STATCRED",
            "SCREDAMT",
            "ZONECODE",
            "USEGROUP",
            "DHCDUSE1",
            "DWELUNIT",
            "NO_IMPRV",
            "VACIND",
            "OWNER_1",
            "OWNER_2",
            "FULLADDR",
            "NEIGHBOR",
            "PROPDESC",
            "YEAR_BUILD",
            "STRUCTAREA",
            "LOT_SIZE",
        ]


        def fetch_arcgis_records(query_url, where="1=1", out_fields=None, chunk_size=1000, return_geometry=False):
            session = requests.Session()
            count_resp = session.get(
                query_url,
                params={"f": "json", "where": where, "returnCountOnly": "true"},
                timeout=60,
            )
            count_resp.raise_for_status()
            total_records = count_resp.json()["count"]
            print(f"Total records matching filter: {total_records:,}")

            rows = []
            for offset in range(0, total_records, chunk_size):
                params = {
                    "f": "json",
                    "where": where,
                    "outFields": "*" if out_fields is None else ",".join(out_fields),
                    "returnGeometry": str(return_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": chunk_size,
                    "orderByFields": "OBJECTID ASC",
                }
                if return_geometry:
                    params["outSR"] = 4326
                    params["geometryPrecision"] = 6

                response = session.get(query_url, params=params, timeout=180)
                response.raise_for_status()
                payload = response.json()
                features = payload.get("features", [])
                if not features:
                    break
                rows.extend(features)
                if offset == 0 or ((offset // chunk_size) + 1) % 25 == 0 or offset + chunk_size >= total_records:
                    print(f"Fetched {min(offset + len(features), total_records):,} / {total_records:,}")

            return rows


        def esri_polygon_to_shapely(geometry_dict):
            rings = geometry_dict.get("rings", [])
            if not rings:
                return None
            if len(rings) == 1:
                return Polygon(rings[0])
            return Polygon(rings[0], holes=rings[1:])


        def load_attrs():
            if attrs_cache.exists():
                print(f"Loading attribute cache: {attrs_cache.name}")
                return pd.read_parquet(attrs_cache)

            features = fetch_arcgis_records(parcel_query_url, out_fields=attr_fields, chunk_size=1000)
            df = pd.DataFrame([feature["attributes"] for feature in features])
            df = df.drop_duplicates(subset=["OBJECTID"]).sort_values("OBJECTID").reset_index(drop=True)
            df.to_parquet(attrs_cache, index=False)
            print(f"Saved attribute cache: {attrs_cache.name}")
            return df


        def load_geometry():
            if geometry_cache.exists():
                print(f"Loading geometry cache: {geometry_cache.name}")
                return gpd.read_parquet(geometry_cache)

            features = fetch_arcgis_records(
                parcel_query_url,
                out_fields=["OBJECTID", "PIN"],
                chunk_size=1000,
                return_geometry=True,
            )
            rows = []
            for feature in features:
                attrs = feature["attributes"]
                geom = esri_polygon_to_shapely(feature["geometry"])
                rows.append(
                    {
                        "OBJECTID": attrs["OBJECTID"],
                        "PIN": attrs["PIN"],
                        "geometry": geom,
                    }
                )
            gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
            gdf = gdf.drop_duplicates(subset=["OBJECTID"]).sort_values("OBJECTID").reset_index(drop=True)
            gdf.to_parquet(geometry_cache, index=False)
            print(f"Saved geometry cache: {geometry_cache.name}")
            return gdf
        """
    ),
    md(
        """
        ## Step 1: Load Parcel Data

        Baltimore parcel data comes from Baltimore City's `Realproperty_OB` ArcGIS FeatureServer:

        - Base service: `https://geodata.baltimorecity.gov/egis/rest/services/CityView/Realproperty_OB/FeatureServer`
        - Parcel layer: `0`
        - Geography: city-only dataset, so no county filter is required

        The main parcel layer already includes:

        - current assessed land / improvement values (`CURRLAND`, `CURRIMPR`)
        - taxable land / improvement components (`BFCVLAND`, `BFCVIMPR`)
        - total taxable base (`ARTAXBAS`)
        - actual city levy amount (`CITY_TAX`)

        The notebook uses the `BFCV*` and `ARTAXBAS` fields for current-law reconstruction because they most closely match the taxable base the city levy is actually applied to.
        """
    ),
    code(
        """
        parcel_attrs = load_attrs()
        parcel_geometry = load_geometry()

        gdf = parcel_geometry.merge(parcel_attrs, on=["OBJECTID", "PIN"], how="inner")
        gdf = gdf.drop_duplicates(subset=["OBJECTID"]).sort_values("OBJECTID").reset_index(drop=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")

        numeric_cols = [
            "CURRLAND",
            "CURRIMPR",
            "EXMPLAND",
            "EXMPIMPR",
            "BFCVLAND",
            "BFCVIMPR",
            "ARTAXBAS",
            "CITY_TAX",
            "CITYCRED",
            "CCREDAMT",
            "STATCRED",
            "SCREDAMT",
            "DWELUNIT",
            "YEAR_BUILD",
            "STRUCTAREA",
        ]
        for col in numeric_cols:
            if col in gdf.columns:
                gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0)

        for col in ["ZONECODE", "USEGROUP", "DHCDUSE1", "NO_IMPRV", "VACIND", "OWNER_1", "OWNER_2", "FULLADDR", "NEIGHBOR", "PROPDESC"]:
            if col in gdf.columns:
                gdf[col] = gdf[col].fillna("").astype(str).str.strip()

        gdf["CURRFMV"] = gdf["CURRLAND"] + gdf["CURRIMPR"]
        gdf["EXMPFMV"] = gdf["EXMPLAND"] + gdf["EXMPIMPR"]
        gdf["BFCVFMV"] = gdf["BFCVLAND"] + gdf["BFCVIMPR"]
        gdf["owner_name"] = gdf[["OWNER_1", "OWNER_2"]].replace("", np.nan).bfill(axis=1).iloc[:, 0].fillna("")
        gdf["full_exmp"] = ((gdf["ARTAXBAS"] <= 0) | (gdf["BFCVFMV"] <= 0)).astype(int)

        print(gdf.shape)
        display(gdf.head(3))
        """
    ),
    md(
        """
        ## Step 2: Validate the Current Baltimore Levy

        The key Baltimore modeling question is what base the city levy is actually applied to. The parcel file contains both:

        - raw current values: `CURRLAND` and `CURRIMPR`
        - taxable components: `BFCVLAND`, `BFCVIMPR`, and `ARTAXBAS`

        Since `CITY_TAX` is the observed current city levy, the notebook checks whether `BFCVLAND + BFCVIMPR` reproduces `ARTAXBAS` and derives the implied city millage directly from `CITY_TAX / ARTAXBAS`.
        """
    ),
    code(
        """
        taxable_components_equal = (gdf["BFCVLAND"] + gdf["BFCVIMPR"]).eq(gdf["ARTAXBAS"])
        exact_match_share = taxable_components_equal.mean() * 100

        positive_base = gdf["ARTAXBAS"] > 0
        implied_rate_series = pd.Series(
            np.where(positive_base, gdf["CITY_TAX"] / gdf["ARTAXBAS"] * 1000.0, np.nan)
        ).replace([np.inf, -np.inf], np.nan)

        validation_summary = pd.DataFrame(
            {
                "metric": [
                    "Parcels",
                    "Fully exempt / zero taxable base",
                    "Share where BFCVLAND + BFCVIMPR == ARTAXBAS",
                    "Sum ARTAXBAS",
                    "Sum CITY_TAX",
                    "Implied city millage from totals",
                    "Median parcel implied millage",
                ],
                "value": [
                    f"{len(gdf):,}",
                    f"{int(gdf['full_exmp'].sum()):,}",
                    f"{exact_match_share:.2f}%",
                    f"${gdf['ARTAXBAS'].sum():,.0f}",
                    f"${gdf['CITY_TAX'].sum():,.0f}",
                    f"{(gdf['CITY_TAX'].sum() / gdf['ARTAXBAS'].sum()) * 1000.0:.4f}",
                    f"{implied_rate_series.dropna().median():.4f}",
                ],
            }
        )

        display(validation_summary)
        display(implied_rate_series.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_frame("parcel_implied_millage"))
        """
    ),
    code(
        """
        city_millage = round((gdf["CITY_TAX"].sum() / gdf["ARTAXBAS"].sum()) * 1000.0, 4)
        print(f"Using Baltimore city millage: {city_millage:.4f} mills")

        gdf["city_millage"] = city_millage
        target_revenue = float(gdf["CITY_TAX"].sum())

        current_revenue, _, gdf = calculate_current_tax(
            df=gdf,
            tax_value_col="ARTAXBAS",
            millage_rate_col="city_millage",
            exemption_flag_col="full_exmp",
        )

        gdf["modeled_current_tax"] = gdf["current_tax"]
        gdf["observed_city_tax"] = gdf["CITY_TAX"]
        gdf["current_tax_gap"] = gdf["modeled_current_tax"] - gdf["observed_city_tax"]
        gdf["current_tax"] = gdf["observed_city_tax"]

        print(f"Modeled current revenue from ARTAXBAS: ${current_revenue:,.2f}")
        print(f"Observed CITY_TAX sum:               ${target_revenue:,.2f}")
        print(f"Absolute revenue gap:                ${abs(current_revenue - target_revenue):,.2f}")
        print(f"Median parcel gap:       ${gdf['current_tax_gap'].median():,.4f}")
        print(f"95th percentile gap:     ${gdf['current_tax_gap'].abs().quantile(0.95):,.4f}")
        """
    ),
    md(
        """
        ## Step 3: Build Baltimore Property Categories

        The modeling guide notes that Baltimore notebooks often use `ZONECODE` for the main category mapping. This notebook uses a Baltimore-specific hybrid mapping:

        - `ZONECODE` supplies the main zoning family
        - `USEGROUP` and `DWELUNIT` split residential parcels into single-family / small multi-family / large multi-family
        - parcels with no improvements or zero taxable building value are classified as `Vacant Land`

        The goal is not to reproduce zoning law exactly, but to create stable analytical categories for the tax-impact charts.
        """
    ),
    code(
        """
        def categorize_baltimore_property(row):
            zone = str(row.get("ZONECODE", "")).strip().upper()
            usegroup = str(row.get("USEGROUP", "")).strip().upper()
            dwell_units = pd.to_numeric(row.get("DWELUNIT", 0), errors="coerce")
            curr_impr = pd.to_numeric(row.get("CURRIMPR", 0), errors="coerce")
            taxable_impr = pd.to_numeric(row.get("BFCVIMPR", 0), errors="coerce")
            no_imprv = str(row.get("NO_IMPRV", "")).strip().upper()

            if (curr_impr <= 0) or (taxable_impr <= 0) or (no_imprv == "Y"):
                return "Vacant Land"

            if usegroup == "R":
                if dwell_units <= 1:
                    return "Single Family Residential"
                if 2 <= dwell_units <= 4:
                    return "Small Multi-Family (2-4 units)"
                if dwell_units >= 5:
                    return "Large Multi-Family (5+ units)"
                return "Other Residential"

            if zone.startswith("R-"):
                return "Other Residential"

            if zone.startswith("I-"):
                return "Industrial"

            if zone.startswith("OR-") or zone.startswith("C-") or zone.startswith("EC-") or zone.startswith("CC") or zone.startswith("PC-") or zone.startswith("TOD-") or zone in {"BSC", "IMU-1", "MI", "H", "OS"}:
                return "Commercial / Mixed Use"

            if usegroup in {"C", "CC", "CR", "RC", "EC"}:
                return "Commercial / Mixed Use"

            if usegroup == "I":
                return "Industrial"

            if usegroup == "U":
                return "Utility / Special"

            if usegroup == "E":
                return "Institutional / Exempt"

            if usegroup == "M":
                return "Large Multi-Family (5+ units)"

            return "Other"


        gdf["PROPERTY_CATEGORY"] = gdf.apply(categorize_baltimore_property, axis=1)

        display(
            gdf["PROPERTY_CATEGORY"]
            .value_counts(dropna=False)
            .rename_axis("PROPERTY_CATEGORY")
            .reset_index(name="parcel_count")
        )
        """
    ),
    md(
        """
        ## Step 4: Model Revenue-Neutral LVT Scenarios

        Baltimore's reference scenario in the guide is `2:1`, so that is the primary exhibit. Additional scenarios show the effect of moving further toward land taxation while keeping the **same city revenue target**.

        Because the Baltimore parcel file already provides taxable land and building components (`BFCVLAND`, `BFCVIMPR`), those are the components used for the split-rate modeling rather than the uncapped current values.
        """
    ),
    code(
        """
        def run_split_rate_scenario(df_input, ratio):
            land_millage, improvement_millage, new_revenue, modeled = model_split_rate_tax(
                df=df_input,
                land_value_col="BFCVLAND",
                improvement_value_col="BFCVIMPR",
                current_revenue=target_revenue,
                land_improvement_ratio=ratio,
                exemption_flag_col="full_exmp",
            )
            return {
                "scenario": f"Split-rate {ratio}:1",
                "land_millage": land_millage,
                "improvement_millage": improvement_millage,
                "new_revenue": new_revenue,
                "median_pct_change": modeled["tax_change_pct"].median(),
                "mean_pct_change": modeled["tax_change_pct"].mean(),
                "df": modeled,
            }


        def run_land_only_scenario(df_input):
            modeled = df_input.copy()
            modeled["taxable_land_only"] = modeled["BFCVLAND"].clip(lower=0)

            land_only_millage = (target_revenue * 1000.0) / modeled["taxable_land_only"].sum()
            modeled["new_tax_before_credits"] = (modeled["taxable_land_only"] * land_only_millage / 1000.0).clip(lower=0)
            modeled["new_tax"] = modeled["new_tax_before_credits"]
            modeled["tax_change"] = modeled["new_tax"] - modeled["current_tax"]
            modeled["tax_change_pct"] = np.where(
                modeled["current_tax"] != 0,
                (modeled["tax_change"] / modeled["current_tax"]) * 100.0,
                0.0,
            )
            modeled["land_tax_before_credits"] = modeled["new_tax_before_credits"]
            modeled["improvement_tax_before_credits"] = 0.0
            return {
                "scenario": "Land-only",
                "land_millage": land_only_millage,
                "improvement_millage": 0.0,
                "new_revenue": modeled["new_tax"].sum(),
                "median_pct_change": modeled["tax_change_pct"].median(),
                "mean_pct_change": modeled["tax_change_pct"].mean(),
                "df": modeled,
            }


        scenarios = [
            run_split_rate_scenario(gdf, 2),
            run_split_rate_scenario(gdf, 4),
            run_split_rate_scenario(gdf, 10),
            run_land_only_scenario(gdf),
        ]

        scenario_summary = pd.DataFrame(
            [
                {
                    "scenario": scenario["scenario"],
                    "land_millage": scenario["land_millage"],
                    "improvement_millage": scenario["improvement_millage"],
                    "new_revenue": scenario["new_revenue"],
                    "revenue_gap": scenario["new_revenue"] - target_revenue,
                    "median_tax_change_pct": scenario["median_pct_change"],
                    "mean_tax_change_pct": scenario["mean_pct_change"],
                }
                for scenario in scenarios
            ]
        )

        display(scenario_summary)
        """
    ),
    code(
        """
        baltimore_2to1 = next(s for s in scenarios if s["scenario"] == "Split-rate 2:1")["df"].copy()

        category_summary = calculate_category_tax_summary(
            df=baltimore_2to1,
            category_col="PROPERTY_CATEGORY",
            current_tax_col="current_tax",
            new_tax_col="new_tax",
            pct_threshold=10.0,
        )

        print_category_tax_summary(
            summary_df=category_summary,
            title="2:1 Split-Rate Tax Impact by Property Category - Baltimore, MD",
            pct_threshold=10.0,
        )

        display(category_summary)
        """
    ),
    md(
        """
        ## Step 5: Property Category Impact Visualizations

        The first chart mirrors the horizontal category bars used in Spokane and Syracuse. The second chart compares the median tax change across the major scenarios for a few policy-relevant categories.
        """
    ),
    code(
        """
        filtered = category_summary[category_summary["property_count"] > 100].copy()
        filtered = filtered.sort_values("median_tax_change_pct")

        colors = np.where(filtered["median_tax_change_pct"] > 0, "#8B0000", "#228B22")
        y = np.arange(len(filtered))

        fig, ax = plt.subplots(figsize=(14, max(6, len(filtered) * 0.65)))
        ax.barh(y, filtered["median_tax_change_pct"], color=colors, alpha=0.92)
        ax.axvline(0, color="black", linewidth=1, linestyle="dotted")

        ax.set_yticks(y)
        ax.set_yticklabels(filtered["PROPERTY_CATEGORY"])
        ax.set_xlabel("Median tax change (%)")
        ax.set_title("Baltimore 2:1 Split-Rate Tax Impact by Property Category")

        for idx, (_, row) in enumerate(filtered.iterrows()):
            ax.text(
                row["median_tax_change_pct"] + (0.5 if row["median_tax_change_pct"] >= 0 else -0.5),
                idx,
                f"{row['median_tax_change_pct']:.1f}%",
                va="center",
                ha="left" if row["median_tax_change_pct"] >= 0 else "right",
                fontsize=10,
                fontweight="bold",
            )

        plt.tight_layout()
        plt.show()
        """
    ),
    code(
        """
        focus_categories = [
            "Single Family Residential",
            "Small Multi-Family (2-4 units)",
            "Large Multi-Family (5+ units)",
            "Commercial / Mixed Use",
            "Vacant Land",
        ]

        scenario_category_rows = []
        for scenario in scenarios:
            summary = calculate_category_tax_summary(
                df=scenario["df"],
                category_col="PROPERTY_CATEGORY",
                current_tax_col="current_tax",
                new_tax_col="new_tax",
                pct_threshold=10.0,
            )
            summary = summary[summary["PROPERTY_CATEGORY"].isin(focus_categories)].copy()
            summary["scenario"] = scenario["scenario"]
            scenario_category_rows.append(summary[["scenario", "PROPERTY_CATEGORY", "median_tax_change_pct"]])

        scenario_category_df = pd.concat(scenario_category_rows, ignore_index=True)
        pivot = scenario_category_df.pivot(index="scenario", columns="PROPERTY_CATEGORY", values="median_tax_change_pct")
        display(pivot)

        pivot.plot(kind="bar", figsize=(13, 6), colormap="RdYlGn_r")
        plt.axhline(0, color="black", linewidth=1, linestyle="dotted")
        plt.ylabel("Median tax change (%)")
        plt.title("Median Tax Change by Scenario and Property Category")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.show()
        """
    ),
    md(
        """
        ## Step 6: Vacant Land and Underused-Land Diagnostics

        The repo's shared policy-analysis helpers make it easy to summarize how much city land value sits in vacant parcels and whether low-improvement parcels are concentrated in places that look like parking / underused land.
        """
    ),
    code(
        """
        vacant_results = analyze_vacant_land(
            df=baltimore_2to1,
            land_value_col="BFCVLAND",
            improvement_value_col="BFCVIMPR",
            property_type_col="PROPERTY_CATEGORY",
            vacant_identifier="Vacant Land",
            neighborhood_col="NEIGHBOR",
            owner_col="owner_name",
            exemption_flag_col="full_exmp",
        )
        print_vacant_land_summary(vacant_results)

        parking_proxy = baltimore_2to1.copy()
        parking_proxy["parking_proxy_category"] = np.where(
            (parking_proxy["PROPERTY_CATEGORY"] == "Commercial / Mixed Use")
            & (parking_proxy["BFCVLAND"] > 0)
            & ((parking_proxy["BFCVIMPR"] / parking_proxy["BFCVLAND"].replace(0, np.nan)).fillna(0) <= 0.15),
            "Transportation - Parking",
            parking_proxy["PROPERTY_CATEGORY"],
        )

        parking_results = analyze_parking_lots(
            df=parking_proxy,
            land_value_col="BFCVLAND",
            improvement_value_col="BFCVIMPR",
            property_type_col="parking_proxy_category",
            parking_identifier="Transportation - Parking",
            exemption_flag_col="full_exmp",
        )
        print_parking_analysis_summary(parking_results)
        """
    ),
    md(
        """
        ## Step 7: Census Merge and Block-Group Equity Analysis

        These cells load Census block-group boundaries for Baltimore city (`24510`) and join parcels to block groups using parcel centroids. You will need `CENSUS_API_KEY` in `.env` for this section to run.
        """
    ),
    code(
        """
        census_data, census_boundaries = get_census_data_with_boundaries(
            fips_code="24510",
            year=2022,
        )

        census_boundaries = census_boundaries.set_crs(epsg=4326)
        df_geo = match_to_census_blockgroups(
            gdf=baltimore_2to1.to_crs(epsg=4326),
            census_gdf=census_boundaries,
            join_type="left",
        )

        print(f"Block groups loaded: {len(census_boundaries):,}")
        print(f"Parcels with census join rows: {len(df_geo):,}")
        display(df_geo.head(3))
        """
    ),
    code(
        """
        bg_summary = calculate_block_group_summary(
            df=df_geo,
            group_col="std_geoid",
            tax_change_col="tax_change",
            current_tax_col="current_tax",
            new_tax_col="new_tax",
        )

        display(bg_summary.head())
        """
    ),
    code(
        """
        bg_map = census_boundaries.merge(
            bg_summary[["std_geoid", "mean_tax_change_pct", "median_income", "minority_pct", "parcel_count"]],
            on="std_geoid",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(10, 10))
        bg_map.plot(
            column="mean_tax_change_pct",
            cmap="RdYlGn_r",
            linewidth=0.15,
            edgecolor="white",
            legend=True,
            ax=ax,
            missing_kwds={"color": "#d9d9d9", "label": "No data"},
        )
        ax.set_title("Mean Parcel Tax Change by Census Block Group (Baltimore 2:1)")
        ax.set_axis_off()
        plt.tight_layout()
        plt.show()
        """
    ),
    code(
        """
        def create_quintile_summary(df_input, value_col, labels=None):
            if labels is None:
                labels = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]

            work = df_input[df_input[value_col].notna()].copy()
            if value_col == "median_income":
                work = work[work[value_col] > 0].copy()

            work["quintile"] = pd.qcut(work[value_col], 5, labels=labels, duplicates="drop")
            summary = work.groupby("quintile").agg(
                count=("tax_change", "count"),
                mean_tax_change=("tax_change", "mean"),
                median_tax_change=("tax_change", "median"),
                mean_tax_change_pct=("tax_change_pct", "mean"),
                median_tax_change_pct=("tax_change_pct", "median"),
                mean_value=(value_col, "mean"),
            ).reset_index()
            return summary


        def plot_upside_down_quintile_bars(summary_df, title):
            vals = summary_df["median_tax_change_pct"].astype(float)
            labels = summary_df["quintile"]

            fig, ax = plt.subplots(figsize=(10, 6))
            colors = sns.color_palette("Greens", n_colors=len(vals))
            color_map = [colors[i] for i in np.argsort(np.argsort(-vals))]

            bars = ax.bar(labels, np.abs(vals), color=color_map, edgecolor="black", width=0.7)
            ax.invert_yaxis()
            ax.yaxis.set_visible(False)
            ax.set_ylabel("")
            ax.set_xlabel("")
            ax.set_title(title, weight="bold", pad=30)
            sns.despine(left=True, right=True, top=True, bottom=True)

            for bar, val in zip(bars, vals):
                ax.annotate(
                    f"{val:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2),
                    xytext=(0, 0),
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    fontsize=13,
                    color="black",
                    fontweight="bold",
                )

            ax.xaxis.set_ticks_position("top")
            ax.xaxis.set_label_position("top")
            plt.xticks(fontweight="bold")

            ymax = np.abs(vals).max() * 1.1 if len(vals) else 1
            ax.set_ylim(ymax, 0)

            plt.tight_layout()
            plt.show()
        """
    ),
    code(
        """
        non_vacant_gdf = df_geo[df_geo["PROPERTY_CATEGORY"] != "Vacant Land"].copy()

        non_vacant_income_quintile_summary = create_quintile_summary(non_vacant_gdf, "median_income")
        non_vacant_minority_quintile_summary = create_quintile_summary(non_vacant_gdf, "minority_pct")

        display(non_vacant_income_quintile_summary)
        display(non_vacant_minority_quintile_summary)

        plot_upside_down_quintile_bars(
            non_vacant_income_quintile_summary,
            "Median Tax Change by Neighborhood Median Income (Excl. Vacant Land)",
        )

        plot_upside_down_quintile_bars(
            non_vacant_minority_quintile_summary,
            "Median Tax Change by Minority Percentage Quintile (Excl. Vacant Land)",
        )
        """
    ),
    md(
        """
        ## Step 8: Residential-Only Progressivity Cuts

        As in the Cleveland notebook, the last section reruns the quintile analysis for:

        - single-family homes only
        - all residential parcels only
        """
    ),
    code(
        """
        single_family = df_geo[df_geo["PROPERTY_CATEGORY"] == "Single Family Residential"].copy()
        residential_categories = [
            "Single Family Residential",
            "Small Multi-Family (2-4 units)",
            "Large Multi-Family (5+ units)",
            "Other Residential",
        ]
        all_residential = df_geo[df_geo["PROPERTY_CATEGORY"].isin(residential_categories)].copy()

        sf_income = create_quintile_summary(single_family, "median_income")
        sf_minority = create_quintile_summary(single_family, "minority_pct")
        res_income = create_quintile_summary(all_residential, "median_income")
        res_minority = create_quintile_summary(all_residential, "minority_pct")

        display(sf_income)
        display(sf_minority)
        display(res_income)
        display(res_minority)
        """
    ),
    code(
        """
        plot_upside_down_quintile_bars(
            sf_income,
            "Median Tax Change by Neighborhood Median Income (Single Family Only)",
        )
        plot_upside_down_quintile_bars(
            sf_minority,
            "Median Tax Change by Minority Percentage Quintile (Single Family Only)",
        )
        plot_upside_down_quintile_bars(
            res_income,
            "Median Tax Change by Neighborhood Median Income (All Residential)",
        )
        plot_upside_down_quintile_bars(
            res_minority,
            "Median Tax Change by Minority Percentage Quintile (All Residential)",
        )
        """
    ),
]

nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "version": "3.11",
    },
}

NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
with NOTEBOOK_PATH.open("w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Wrote {NOTEBOOK_PATH}")
