import json
from pathlib import Path
from textwrap import dedent

NOTEBOOK_PATH = Path("examples/greeley.ipynb")


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [dedent(text).strip() + "\n"],
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [dedent(text).strip() + "\n"],
    }


cells = [
    md(
        """
        # Greeley, CO LVT Shift Notebook

        This notebook sets up a Greeley-specific LVT workflow using the Weld County open parcel layer and the extraction guidance in `examples/skills/greeley/FETCH.md`.

        Policy defaults used in this setup (can be changed later):

        - Scope: city parcels where `LOCCITY = 'GREELEY'`
        - Reform type: split-rate LVT scenarios
        - Existing tax structure: preserved conceptually, but this starter uses a placeholder current tax proxy until a district-level mill levy table is merged
        """
    ),
    code(
        """
        import sys
        from pathlib import Path

        import geopandas as gpd
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import requests
        import seaborn as sns
        from shapely.geometry import Polygon

        REPO_ROOT = Path.cwd()
        if not (REPO_ROOT / "lvt_utils.py").exists():
            REPO_ROOT = REPO_ROOT.parent

        if str(REPO_ROOT) not in sys.path:
            sys.path.append(str(REPO_ROOT))

        from lvt_utils import (
            calculate_category_tax_summary,
            model_split_rate_tax,
            print_category_tax_summary,
        )
        from policy_analysis import (
            analyze_land_by_improvement_share,
            analyze_parking_lots,
            analyze_vacant_land,
            print_parking_analysis_summary,
            print_vacant_land_summary,
        )
        from census_utils import get_census_data_with_boundaries, match_to_census_blockgroups
        from viz import create_quintile_summary

        sns.set_theme(style="whitegrid")
        pd.set_option("display.max_columns", 200)
        pd.set_option("display.max_rows", 120)
        """
    ),
    code(
        """
        data_dir = REPO_ROOT / "examples" / "data" / "greeley"
        data_dir.mkdir(parents=True, exist_ok=True)

        endpoint = "https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/Parcels_open_data/FeatureServer/0/query"
        city_filter = "LOCCITY = 'GREELEY'"
        page_size = 2000

        attrs_cache = data_dir / "greeley_attrs_20260413.parquet"
        geometry_cache = data_dir / "greeley_geometry_20260413.parquet"

        attr_fields = [
            "OBJECTID", "PARCEL", "ACCOUNTNO", "ACCTTYPE", "ACCOUNTTYP", "NAME", "SITUS", "LOCCITY", "LEGAL",
            "LANDACT", "IMPACT", "TOTALACT", "LANDASD", "IMPASD", "TOTALASD", "LGLANDASD", "LGIMPASD",
            "TOTALLGASD", "SCLANDASD", "SCIMPASD", "TOTALSCASD", "ASSRCODE", "SALEP", "SALEDT", "GIS_Acres",
            "latitude", "longitude", "Shape__Area", "Shape__Length",
        ]


        def fetch_arcgis_records(query_url, where, out_fields, chunk_size=2000, return_geometry=False):
            session = requests.Session()

            count_resp = session.get(
                query_url,
                params={"f": "json", "where": where, "returnCountOnly": "true"},
                timeout=60,
            )
            count_resp.raise_for_status()
            total_records = int(count_resp.json().get("count", 0))
            print(f"Total records matching filter: {total_records:,}")

            rows = []
            for offset in range(0, total_records, chunk_size):
                params = {
                    "f": "json",
                    "where": where,
                    "outFields": ",".join(out_fields),
                    "returnGeometry": str(return_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": chunk_size,
                    "orderByFields": "OBJECTID ASC",
                }
                if return_geometry:
                    params["outSR"] = 4326
                    params["geometryPrecision"] = 6

                resp = session.get(query_url, params=params, timeout=180)
                resp.raise_for_status()
                payload = resp.json()
                features = payload.get("features", [])
                if not features:
                    break

                rows.extend(features)
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

            features = fetch_arcgis_records(endpoint, city_filter, attr_fields, chunk_size=page_size)
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
                endpoint,
                city_filter,
                ["OBJECTID", "PARCEL"],
                chunk_size=page_size,
                return_geometry=True,
            )
            rows = []
            for feature in features:
                attrs = feature["attributes"]
                rows.append(
                    {
                        "OBJECTID": attrs["OBJECTID"],
                        "PARCEL": attrs["PARCEL"],
                        "geometry": esri_polygon_to_shapely(feature.get("geometry", {})),
                    }
                )

            gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
            gdf = gdf.drop_duplicates(subset=["OBJECTID"]).sort_values("OBJECTID").reset_index(drop=True)
            gdf.to_parquet(geometry_cache, index=False)
            print(f"Saved geometry cache: {geometry_cache.name}")
            return gdf
        """
    ),
    md("## Step 1: Fetch and load Greeley parcels"),
    code(
        """
        parcel_attrs = load_attrs()
        parcel_geom = load_geometry()

        gdf = parcel_geom.merge(parcel_attrs, on=["OBJECTID", "PARCEL"], how="inner")
        gdf = gdf.drop_duplicates(subset=["OBJECTID"]).sort_values("OBJECTID").reset_index(drop=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")

        numeric_cols = [
            "LANDACT", "IMPACT", "TOTALACT", "LANDASD", "IMPASD", "TOTALASD", "LGLANDASD", "LGIMPASD",
            "TOTALLGASD", "SCLANDASD", "SCIMPASD", "TOTALSCASD", "SALEP", "GIS_Acres",
        ]
        for col in numeric_cols:
            if col in gdf.columns:
                gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0)

        print(gdf.shape)
        display(gdf[["PARCEL", "ACCOUNTNO", "ACCTTYPE", "LOCCITY", "LANDACT", "IMPACT", "TOTALACT"]].head(5))
        """
    ),
    md("## Step 2: Basic quality checks and helper fields"),
    code(
        """
        gdf["actual_total_check"] = gdf["LANDACT"] + gdf["IMPACT"]
        gdf["assessed_total_check"] = gdf["LANDASD"] + gdf["IMPASD"]
        gdf["actual_diff"] = gdf["TOTALACT"] - gdf["actual_total_check"]
        gdf["assessed_diff"] = gdf["TOTALASD"] - gdf["assessed_total_check"]

        print("Max absolute actual mismatch:", gdf["actual_diff"].abs().max())
        print("Max absolute assessed mismatch:", gdf["assessed_diff"].abs().max())

        gdf["assessed_to_actual_ratio"] = np.where(gdf["TOTALACT"] > 0, gdf["TOTALASD"] / gdf["TOTALACT"], 0)
        gdf["price_per_acre"] = np.where(gdf["GIS_Acres"] > 0, gdf["SALEP"] / gdf["GIS_Acres"], 0)

        display(gdf[["TOTALACT", "TOTALASD", "assessed_to_actual_ratio", "price_per_acre"]].describe())
        """
    ),
    md("## Step 3: Property categories for summary output"),
    code(
        """
        def map_property_category(accttype: str) -> str:
            value = str(accttype).upper()
            if "VAC" in value or "VACANT" in value:
                return "Vacant / Undeveloped"
            if "RES" in value or "SINGLE" in value or "CONDO" in value:
                return "Residential"
            if "COMM" in value or "RETAIL" in value or "OFFICE" in value:
                return "Commercial"
            if "IND" in value:
                return "Industrial"
            if "EXEM" in value or "GOV" in value:
                return "Exempt / Government"
            return "Other"


        gdf["PROPERTY_CATEGORY"] = gdf["ACCTTYPE"].apply(map_property_category)
        display(gdf["PROPERTY_CATEGORY"].value_counts().to_frame("parcel_count"))
        """
    ),
    md("## Step 4: Revenue-neutral split-rate scenarios (starter)"),
    code(
        """
        model_df = gdf.copy()
        model_df["current_tax_proxy"] = model_df["TOTALASD"] / 1000.0
        model_df["current_tax"] = model_df["current_tax_proxy"]
        current_revenue = model_df["current_tax"].sum()

        scenario_outputs = {}
        for ratio in [2, 4, 8]:
            land_mill, imp_mill, revenue, scenario_df = model_split_rate_tax(
                df=model_df.copy(),
                land_value_col="LANDASD",
                improvement_value_col="IMPASD",
                current_revenue=current_revenue,
                land_improvement_ratio=ratio,
            )
            new_col = f"tax_shift_{ratio}to1"
            scenario_df[new_col] = scenario_df["new_tax"] - scenario_df["current_tax"]
            scenario_outputs[ratio] = {
                "land_mill": land_mill,
                "imp_mill": imp_mill,
                "revenue": revenue,
                "df": scenario_df,
                "new_col": new_col,
            }
            print(f"{ratio}:1 split -> land mill {land_mill:.4f}, imp mill {imp_mill:.4f}, revenue {revenue:,.2f}")
        """
    ),
    code(
        """
        primary = scenario_outputs[4]["df"].copy()
        primary["tax_change"] = primary["new_tax"] - primary["current_tax"]
        primary["tax_change_pct"] = np.where(
            primary["current_tax"] > 0,
            (primary["tax_change"] / primary["current_tax"]) * 100,
            0,
        )

        summary = calculate_category_tax_summary(
            df=primary,
            category_col="PROPERTY_CATEGORY",
            current_tax_col="current_tax",
            new_tax_col="new_tax",
        )
        print_category_tax_summary(summary)

        plot_df = (
            primary.groupby("PROPERTY_CATEGORY", as_index=False)["tax_shift_4to1"]
            .mean()
            .sort_values("tax_shift_4to1")
        )
        plt.figure(figsize=(10, 5))
        sns.barplot(data=plot_df, x="tax_shift_4to1", y="PROPERTY_CATEGORY", color="#2a6fbb")
        plt.axvline(0, color="black", linewidth=1)
        plt.title("Average parcel tax change by category (4:1 split, proxy baseline)")
        plt.xlabel("Average tax change")
        plt.ylabel("Property category")
        plt.tight_layout()
        plt.show()
        """
    ),
    md("## Step 5: Land-use diagnostics (vacancy, parking, low-improvement share)"),
    code(
        """
        analysis_df = primary.copy()
        analysis_df["LAND_USE_FOR_ANALYSIS"] = np.select(
            [
                analysis_df["ACCTTYPE"].astype(str).str.upper().str.contains("VAC", na=False),
                analysis_df["ACCTTYPE"].astype(str).str.upper().str.contains("PARK", na=False),
            ],
            ["Vacant Land", "Trans - Parking"],
            default="Other",
        )

        vacant_results = analyze_vacant_land(
            df=analysis_df,
            land_value_col="LANDASD",
            improvement_value_col="IMPASD",
            property_type_col="LAND_USE_FOR_ANALYSIS",
            vacant_identifier="Vacant Land",
            owner_col="NAME",
        )
        print_vacant_land_summary(vacant_results)

        parking_results = analyze_parking_lots(
            df=analysis_df,
            land_value_col="LANDASD",
            improvement_value_col="IMPASD",
            property_type_col="LAND_USE_FOR_ANALYSIS",
            parking_identifier="Trans - Parking",
            min_land_value_threshold=50000,
            max_improvement_ratio=0.10,
        )
        print_parking_analysis_summary(parking_results)

        low_impr_share = analyze_land_by_improvement_share(
            df=analysis_df,
            land_value_col="LANDASD",
            improvement_value_col="IMPASD",
        )
        display(pd.DataFrame(low_impr_share["categories"]))
        """
    ),
    md("## Step 6: Tax-shift distribution and high-impact parcels"),
    code(
        """
        plt.figure(figsize=(10, 5))
        sns.histplot(primary["tax_change"], bins=80, kde=True, color="#2a6fbb")
        plt.axvline(0, color="black", linewidth=1)
        plt.title("Distribution of parcel-level tax changes (4:1)")
        plt.xlabel("Tax change")
        plt.ylabel("Parcel count")
        plt.tight_layout()
        plt.show()

        top_increase = primary.nlargest(20, "tax_change")[
            ["PARCEL", "ACCOUNTNO", "ACCTTYPE", "LANDASD", "IMPASD", "current_tax", "new_tax", "tax_change", "tax_change_pct"]
        ]
        top_decrease = primary.nsmallest(20, "tax_change")[
            ["PARCEL", "ACCOUNTNO", "ACCTTYPE", "LANDASD", "IMPASD", "current_tax", "new_tax", "tax_change", "tax_change_pct"]
        ]

        print("Top 20 increases")
        display(top_increase)
        print("Top 20 decreases")
        display(top_decrease)
        """
    ),
    md("## Step 7: Census equity analysis (Weld County block groups, FIPS 08123)"),
    code(
        """
        equity_df = primary.copy()
        equity_df = equity_df.to_crs(epsg=4326)

        try:
            census_data, census_boundaries = get_census_data_with_boundaries(
                fips_code="08123",
                year=2022,
            )
            matched = match_to_census_blockgroups(equity_df, census_boundaries, join_type="left")
            matched = matched[matched["median_income"] > 0].copy()

            income_quintile_summary = create_quintile_summary(
                matched,
                group_col="median_income",
                value_col="median_income",
                tax_change_col="tax_change",
                tax_change_pct_col="tax_change_pct",
            )
            minority_quintile_summary = create_quintile_summary(
                matched,
                group_col="minority_pct",
                value_col="minority_pct",
                tax_change_col="tax_change",
                tax_change_pct_col="tax_change_pct",
            )

            display(income_quintile_summary)
            display(minority_quintile_summary)

            plt.figure(figsize=(10, 5))
            plt.plot(income_quintile_summary["median_income_quintile"], income_quintile_summary["mean_tax_change_pct"], marker="o")
            plt.axhline(0, color="black", linewidth=1, linestyle="dotted")
            plt.title("Mean tax change percent by neighborhood income quintile")
            plt.xlabel("Income quintile")
            plt.ylabel("Mean tax change (%)")
            plt.tight_layout()
            plt.show()

            plt.figure(figsize=(10, 5))
            plt.plot(minority_quintile_summary["minority_pct_quintile"], minority_quintile_summary["mean_tax_change_pct"], marker="o")
            plt.axhline(0, color="black", linewidth=1, linestyle="dotted")
            plt.title("Mean tax change percent by minority-share quintile")
            plt.xlabel("Minority-share quintile")
            plt.ylabel("Mean tax change (%)")
            plt.tight_layout()
            plt.show()
        except Exception as exc:
            print("Census equity analysis skipped:", exc)
            print("Set CENSUS_API_KEY in .env (or pass api_key) and rerun this cell.")
        """
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
print(f"Wrote {NOTEBOOK_PATH}")
