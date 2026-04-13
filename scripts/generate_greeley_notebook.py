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

        analysis_gdf = gdf[gdf["PROPERTY_CATEGORY"] != "Exempt / Government"].copy()
        print(f"Excluded exempt/government parcels: {len(gdf) - len(analysis_gdf):,}")
        print(f"Parcels used for modeling/analysis: {len(analysis_gdf):,}")
        """
    ),
    md("## Step 4: Revenue-neutral split-rate scenarios (starter)"),
    code(
        """
        model_df = analysis_gdf.copy()
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
    md("## Step 5: Calculate IR, Split Tax Capacity, Run Model"),
    code(
        """
        greeley_city = analysis_gdf.copy()
        greeley_city["IR"] = np.where(greeley_city["TOTALASD"] > 0, greeley_city["IMPASD"] / greeley_city["TOTALASD"], 0)
        greeley_city["TaxCapacity"] = greeley_city["TOTALASD"]
        greeley_city["TaxCapacity_Improvements"] = greeley_city["IR"] * greeley_city["TaxCapacity"]
        greeley_city["TaxCapacity_Land"] = (1 - greeley_city["IR"]) * greeley_city["TaxCapacity"]
        greeley_city["current_tax"] = greeley_city["TOTALASD"] / 1000.0
        current_revenue = greeley_city["current_tax"].sum()

        print("Tax Capacity Split Summary:")
        print(f"  Total Tax Capacity:          ${greeley_city['TaxCapacity'].sum():>15,.0f}")
        print(f"  Tax Capacity (Improvements): ${greeley_city['TaxCapacity_Improvements'].sum():>15,.0f}")
        print(f"  Tax Capacity (Land):         ${greeley_city['TaxCapacity_Land'].sum():>15,.0f}")
        print(f"  Land % of Tax Capacity:      {greeley_city['TaxCapacity_Land'].sum() / greeley_city['TaxCapacity'].sum() * 100:.1f}%")

        tc_land_improvement_ratio = 4
        tc_land_millage, tc_imp_millage, tc_split_rate_revenue, greeley_city = model_split_rate_tax(
            df=greeley_city,
            land_value_col="TaxCapacity_Land",
            improvement_value_col="TaxCapacity_Improvements",
            current_revenue=current_revenue,
            land_improvement_ratio=tc_land_improvement_ratio,
        )

        greeley_city["new_tax_tc"] = greeley_city["new_tax"]
        greeley_city["tax_change_tc"] = greeley_city["new_tax_tc"] - greeley_city["current_tax"]
        greeley_city["tax_change_pct_tc"] = np.where(
            greeley_city["current_tax"] > 0,
            (greeley_city["tax_change_tc"] / greeley_city["current_tax"]) * 100,
            0,
        )

        print(f"\\nFull-Bill Split-Rate Model ({tc_land_improvement_ratio}:1 ratio)")
        print(f"  Land Millage:        {tc_land_millage:.6f}")
        print(f"  Improvement Millage: {tc_imp_millage:.6f}")
        print(f"  Current Revenue:     ${current_revenue:,.0f}")
        print(f"  New Revenue:         ${greeley_city['new_tax_tc'].sum():,.0f}")
        print(f"  Revenue neutral:     {abs(current_revenue - greeley_city['new_tax_tc'].sum()) < 1}")

        greeley_city["LAND_DEV_CATEGORY"] = np.where(greeley_city["IR"] == 0, "Vacant Land", "Developed")
        vacant_results = analyze_vacant_land(
            df=greeley_city,
            land_value_col="LANDASD",
            improvement_value_col="IMPASD",
            property_type_col="LAND_DEV_CATEGORY",
            vacant_identifier="Vacant Land",
        )
        underdeveloped = analyze_land_by_improvement_share(
            df=greeley_city,
            land_value_col="LANDASD",
            improvement_value_col="IMPASD",
        )
        total_land_value = greeley_city["LANDASD"].sum()

        print("\\nUndeveloped and Underdeveloped Land")
        print(f"  Total non-exempt land value: ${total_land_value:,.0f}\\n")
        if "error" not in vacant_results:
            print("  Undeveloped (vacant, IR=0):")
            print(f"    {vacant_results['total_vacant_parcels']:,} parcels")
            print(f"    ${vacant_results['total_vacant_land_value']:,.0f} ({vacant_results['vacant_land_pct_of_total']:.1f}% of non-exempt land value)\\n")

        print("  Underdeveloped (by improvement share):")
        for row in underdeveloped["categories"]:
            print(
                f"    {row['category']:<35} {row['parcel_count']:>7,} parcels  "
                f"${row['adjusted_land_value']:>15,.0f}  ({row['share_of_total_land_value_pct']:.1f}%)"
            )
        """
    ),
    md("## Step 6: Category Summary & Charts"),
    code(
        """
        primary = scenario_outputs[4]["df"].copy()
        primary["tax_change"] = primary["new_tax"] - primary["current_tax"]
        primary["tax_change_pct"] = np.where(
            primary["current_tax"] > 0,
            (primary["tax_change"] / primary["current_tax"]) * 100,
            0,
        )

        output_summary = calculate_category_tax_summary(
            df=primary,
            category_col="PROPERTY_CATEGORY",
            current_tax_col="current_tax",
            new_tax_col="new_tax",
        )
        print_category_tax_summary(output_summary)

        plot_df = (
            output_summary[output_summary["property_count"] > 50]
            .sort_values("median_tax_change_pct")
            .copy()
        )

        fig_height = max(5, len(plot_df) * 0.7)
        plt.figure(figsize=(12, fig_height))
        bar_colors = np.where(plot_df["median_tax_change_pct"] < 0, "#228B22", "#8B0000")
        plt.barh(plot_df["PROPERTY_CATEGORY"], plot_df["median_tax_change_pct"], color=bar_colors)
        plt.axvline(0, color="black", linewidth=1)
        plt.title("Median tax change percent by property category (4:1 split)")
        plt.xlabel("Median tax change (%)")
        plt.ylabel("Property category")
        plt.tight_layout()
        plt.show()
        """
    ),
    code(
        """
        # Butterfly chart: percent of parcels increasing/decreasing >10%
        summary_filtered = output_summary[output_summary["property_count"] > 50].copy()
        summary_sorted = summary_filtered.sort_values("pct_increase_gt_threshold", ascending=True)

        categories_sorted = summary_sorted["PROPERTY_CATEGORY"].tolist()
        pct_increase_sorted = summary_sorted["pct_increase_gt_threshold"].tolist()
        pct_decrease_sorted = summary_sorted["pct_decrease_gt_threshold"].tolist()

        pct_increase_int = [int(round(x)) for x in pct_increase_sorted]
        pct_decrease_int = [int(round(x)) for x in pct_decrease_sorted]

        y = np.arange(len(categories_sorted))
        fig, ax = plt.subplots(figsize=(8, 6))

        color_increase = "#8B0000"
        color_decrease = "#228B22"

        ax.barh(y, [-v for v in pct_decrease_sorted], color=color_decrease, edgecolor="none", height=0.7)
        ax.barh(y, pct_increase_sorted, color=color_increase, edgecolor="none", height=0.7)

        for i, (inc, dec) in enumerate(zip(pct_increase_int, pct_decrease_int)):
            if dec > 0:
                ax.text(-dec - 2, y[i], f"{dec}%", va="center", ha="right", fontsize=8, color=color_decrease)
            if inc > 0:
                ax.text(inc + 2, y[i], f"{inc}%", va="center", ha="left", fontsize=8, color=color_increase)

        for i, (cat, inc) in enumerate(zip(categories_sorted, pct_increase_sorted)):
            xpos = inc + 18 if inc > 0 else 18
            ax.text(xpos, y[i], cat, va="center", ha="left", fontsize=9, fontweight="bold", color="#222")

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        ax.set_yticks([])
        ax.set_xticks([])

        max_val = max(max(pct_increase_sorted), max(pct_decrease_sorted)) if len(pct_increase_sorted) else 10
        ax.set_xlim(-max_val - 20, max_val + 48)

        title_y = len(categories_sorted) - 0.2
        ax.text(-max_val * 0.45, title_y, "Percent of parcels\\ndecreasing >10%", ha="center", va="bottom", fontsize=10)
        ax.text(max_val * 0.45, title_y, "Percent of parcels\\nincreasing >10%", ha="center", va="bottom", fontsize=10)

        plt.tight_layout()
        plt.show()
        """
    ),
    md("## Step 7: Land-use diagnostics (vacancy, parking, low-improvement share)"),
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
    md("## Step 7b: Tax-shift distribution and high-impact parcels"),
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
    md("## Step 8: Census Equity Analysis"),
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

            block_group_summary = (
                matched.groupby("std_geoid")
                .agg(
                    median_income=("median_income", "first"),
                    minority_pct=("minority_pct", "first"),
                    total_current_tax=("current_tax", "sum"),
                    total_new_tax=("new_tax", "sum"),
                    mean_tax_change=("tax_change", "mean"),
                    median_tax_change=("tax_change", "median"),
                    median_tax_change_pct=("tax_change_pct", "median"),
                    parcel_count=("PARCEL", "count"),
                    has_vacant_land=("PROPERTY_CATEGORY", lambda x: (x == "Vacant / Undeveloped").any()),
                )
                .reset_index()
            )
            block_group_summary = block_group_summary[block_group_summary["median_income"] > 0].copy()
            block_group_summary["mean_tax_change_pct"] = np.where(
                block_group_summary["total_current_tax"] > 0,
                ((block_group_summary["total_new_tax"] - block_group_summary["total_current_tax"]) / block_group_summary["total_current_tax"]) * 100,
                0,
            )

            non_vacant_bg = block_group_summary[~block_group_summary["has_vacant_land"]].copy()

            income_quintile_summary = create_quintile_summary(
                block_group_summary,
                group_col="median_income",
                value_col="median_income",
                tax_change_col="mean_tax_change",
                tax_change_pct_col="mean_tax_change_pct",
            )
            non_vacant_income_quintile_summary = create_quintile_summary(
                non_vacant_bg,
                group_col="median_income",
                value_col="median_income",
                tax_change_col="mean_tax_change",
                tax_change_pct_col="mean_tax_change_pct",
            )
            minority_quintile_summary = create_quintile_summary(
                block_group_summary,
                group_col="minority_pct",
                value_col="minority_pct",
                tax_change_col="mean_tax_change",
                tax_change_pct_col="mean_tax_change_pct",
            )
            non_vacant_minority_quintile_summary = create_quintile_summary(
                non_vacant_bg,
                group_col="minority_pct",
                value_col="minority_pct",
                tax_change_col="mean_tax_change",
                tax_change_pct_col="mean_tax_change_pct",
            )

            display(income_quintile_summary)
            display(non_vacant_income_quintile_summary)
            display(minority_quintile_summary)
            display(non_vacant_minority_quintile_summary)

            plt.figure(figsize=(10, 5))
            plt.plot(income_quintile_summary["median_income_quintile"], income_quintile_summary["mean_tax_change_pct"], marker="o", label="All properties")
            plt.plot(non_vacant_income_quintile_summary["median_income_quintile"], non_vacant_income_quintile_summary["mean_tax_change_pct"], marker="o", label="Excluding vacant-land neighborhoods")
            plt.axhline(0, color="black", linewidth=1, linestyle="dotted")
            plt.title("Mean tax change percent by neighborhood income quintile")
            plt.xlabel("Income quintile")
            plt.ylabel("Mean tax change (%)")
            plt.legend()
            plt.tight_layout()
            plt.show()

            plt.figure(figsize=(10, 5))
            plt.plot(minority_quintile_summary["minority_pct_quintile"], minority_quintile_summary["mean_tax_change_pct"], marker="o", label="All properties")
            plt.plot(non_vacant_minority_quintile_summary["minority_pct_quintile"], non_vacant_minority_quintile_summary["mean_tax_change_pct"], marker="o", label="Excluding vacant-land neighborhoods")
            plt.axhline(0, color="black", linewidth=1, linestyle="dotted")
            plt.title("Mean tax change percent by minority-share quintile")
            plt.xlabel("Minority-share quintile")
            plt.ylabel("Mean tax change (%)")
            plt.legend()
            plt.tight_layout()
            plt.show()

            # Inverted bar charts: median tax change by quintile (excluding vacant-land neighborhoods)
            sns.set_theme(style="whitegrid", font_scale=1.15)

            fig, ax = plt.subplots(figsize=(10, 6))
            vals = non_vacant_income_quintile_summary["median_tax_change_pct"]
            labels = non_vacant_income_quintile_summary["median_income_quintile"]
            colors = sns.color_palette("Greens", n_colors=len(vals))
            color_map = [colors[i] for i in np.argsort(np.argsort(-vals))]
            bars = ax.bar(labels, vals, color=color_map, edgecolor="black", width=0.7)
            ax.yaxis.set_visible(False)
            ax.set_title("Median Tax Change by Neighborhood Income (Excl. Vacant)", weight="bold", pad=30)
            sns.despine(left=True, right=True, top=True, bottom=True)
            for bar, val in zip(bars, vals):
                ax.annotate(f"{val:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, val / 2), ha="center", va="center", fontsize=13, fontweight="bold")
            ax.xaxis.set_ticks_position("top")
            ax.xaxis.set_label_position("top")
            plt.xticks(fontweight="bold")
            margin = max(abs(vals.min()), abs(vals.max())) * 1.2 if len(vals) else 1
            ax.set_ylim(-margin, margin)
            ax.axhline(y=0, color="black", linewidth=0.8)
            plt.tight_layout()
            plt.show()

            fig, ax = plt.subplots(figsize=(10, 6))
            vals = non_vacant_minority_quintile_summary["median_tax_change_pct"]
            labels = non_vacant_minority_quintile_summary["minority_pct_quintile"]
            colors = sns.color_palette("Purples", n_colors=len(vals))
            color_map = [colors[i] for i in np.argsort(np.argsort(-vals))]
            bars = ax.bar(labels, vals, color=color_map, edgecolor="black", width=0.7)
            ax.yaxis.set_visible(False)
            ax.set_title("Median Tax Change by Neighborhood Minority % (Excl. Vacant)", weight="bold", pad=30)
            sns.despine(left=True, right=True, top=True, bottom=True)
            for bar, val in zip(bars, vals):
                ax.annotate(f"{val:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, val / 2), ha="center", va="center", fontsize=13, fontweight="bold")
            ax.xaxis.set_ticks_position("top")
            ax.xaxis.set_label_position("top")
            plt.xticks(fontweight="bold")
            margin = max(abs(vals.min()), abs(vals.max())) * 1.2 if len(vals) else 1
            ax.set_ylim(-margin, margin)
            ax.axhline(y=0, color="black", linewidth=0.8)
            plt.tight_layout()
            plt.show()

            # Additional St. Paul-style subgroup quintile charts
            def render_quintile_bars(df_subset, title_prefix):
                if len(df_subset) < 25:
                    print(f"Skipping {title_prefix}: not enough parcels.")
                    return
                inc = create_quintile_summary(
                    df_subset,
                    group_col="median_income",
                    value_col="median_income",
                    tax_change_col="tax_change",
                    tax_change_pct_col="tax_change_pct",
                )
                minor = create_quintile_summary(
                    df_subset,
                    group_col="minority_pct",
                    value_col="minority_pct",
                    tax_change_col="tax_change",
                    tax_change_pct_col="tax_change_pct",
                )
                for summ, lbl_col, palette, ttl in [
                    (inc, "median_income_quintile", "Greens", f"Median Tax Change by Neighborhood Income ({title_prefix})"),
                    (minor, "minority_pct_quintile", "Purples", f"Median Tax Change by Neighborhood Minority % ({title_prefix})"),
                ]:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    vals = summ["median_tax_change_pct"]
                    labels = summ[lbl_col]
                    colors = sns.color_palette(palette, n_colors=len(vals))
                    color_map = [colors[i] for i in np.argsort(np.argsort(-vals))]
                    bars = ax.bar(labels, vals, color=color_map, edgecolor="black", width=0.7)
                    ax.yaxis.set_visible(False)
                    ax.set_title(ttl, weight="bold", pad=30)
                    sns.despine(left=True, right=True, top=True, bottom=True)
                    for bar, val in zip(bars, vals):
                        ax.annotate(f"{val:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, val / 2), ha="center", va="center", fontsize=13, fontweight="bold")
                    ax.xaxis.set_ticks_position("top")
                    ax.xaxis.set_label_position("top")
                    plt.xticks(fontweight="bold")
                    margin = max(abs(vals.min()), abs(vals.max())) * 1.2 if len(vals) else 1
                    ax.set_ylim(-margin, margin)
                    ax.axhline(y=0, color="black", linewidth=0.8)
                    plt.tight_layout()
                    plt.show()

            sfr = matched[matched["PROPERTY_CATEGORY"] == "Residential"].copy()
            mfr = matched[matched["PROPERTY_CATEGORY"].isin(["Residential"])].copy()
            smfr = matched[matched["PROPERTY_CATEGORY"].isin(["Residential"])].copy()

            render_quintile_bars(sfr, "Residential Only")
            render_quintile_bars(mfr, "Multifamily Proxy")
            render_quintile_bars(smfr, "All Residential")
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
