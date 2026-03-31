from pathlib import Path
from textwrap import dedent

import nbformat as nbf


NOTEBOOK_PATH = Path("examples/cleveland.ipynb")


def md(text: str):
    return nbf.v4.new_markdown_cell(dedent(text).strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(dedent(text).strip() + "\n")


nb = nbf.v4.new_notebook()
nb["cells"] = [
    md(
        """
        # Cleveland Levy Policy Example

        This notebook follows the same step structure as the other city notebooks in this repo. It documents the Cleveland-specific implementation choices from `LVT_MODELING_GUIDE.md`, loads parcel data from Cuyahoga County's official GIS services, recreates the current Cleveland city levy, models several LVT scenarios, and produces the same style of property-category and census progressivity charts used in Spokane, Syracuse, Baltimore, and St. Paul.
        """
    ),
    code(
        """
        import os
        import sys
        import time
        from datetime import datetime
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
        pd.set_option("display.max_columns", 120)
        pd.set_option("display.max_rows", 200)
        """
    ),
    code(
        """
        data_dir = REPO_ROOT / "examples" / "data" / "cleveland"
        data_dir.mkdir(parents=True, exist_ok=True)

        parcel_query_url = "https://gis.cuyahogacounty.us/server/rest/services/MyPLACE/Parcels_WMA_GJOIN_WGS84/MapServer/2/query"
        rate_query_url = "https://gis.cuyahogacounty.us/server/rest/services/Hosted/CertEffRates2021/FeatureServer/0/query"
        cleveland_where = "par_city='CLEVELAND'"

        attrs_cache = data_dir / "cleveland_attrs_20260310.parquet"
        geometry_cache = data_dir / "cleveland_geometry_20260310.parquet"

        attr_fields = [
            "objectid",
            "parcel_id",
            "par_addr_all",
            "par_city",
            "parcel_owner",
            "tax_luc",
            "tax_luc_description",
            "property_class",
            "tax_district",
            "neighborhood_code",
            "condo_complex_id",
            "tax_abatement",
            "tax_year",
            "parcel_year",
            "certified_tax_land",
            "certified_tax_building",
            "certified_tax_total",
            "certified_exempt_land",
            "certified_exempt_building",
            "certified_exempt_total",
            "certified_abated_land",
            "certified_abated_building",
            "certified_abated_total",
            "gross_certified_land",
            "gross_certified_building",
            "gross_certified_total",
            "res_bldg_count",
            "com_bldg_count",
            "com_living_units",
            "total_res_liv_area",
            "total_com_use_area",
            "total_square_ft",
            "total_acreage",
        ]


        def fetch_arcgis_records(query_url, where, out_fields, chunk_size=1000, return_geometry=False):
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
                    "outFields": ",".join(out_fields),
                    "returnGeometry": str(return_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": chunk_size,
                    "orderByFields": "objectid ASC",
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

            features = fetch_arcgis_records(parcel_query_url, cleveland_where, attr_fields, chunk_size=1000)
            df = pd.DataFrame([feature["attributes"] for feature in features])
            df = df.drop_duplicates(subset=["objectid"]).sort_values("objectid").reset_index(drop=True)
            df.to_parquet(attrs_cache, index=False)
            print(f"Saved attribute cache: {attrs_cache.name}")
            return df


        def load_geometry():
            if geometry_cache.exists():
                print(f"Loading geometry cache: {geometry_cache.name}")
                return gpd.read_parquet(geometry_cache)

            features = fetch_arcgis_records(
                parcel_query_url,
                cleveland_where,
                ["objectid", "parcel_id"],
                chunk_size=1000,
                return_geometry=True,
            )
            rows = []
            for feature in features:
                attrs = feature["attributes"]
                geom = esri_polygon_to_shapely(feature["geometry"])
                rows.append(
                    {
                        "objectid": attrs["objectid"],
                        "parcel_id": attrs["parcel_id"],
                        "geometry": geom,
                    }
                )
            gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
            gdf = gdf.drop_duplicates(subset=["objectid"]).sort_values("objectid").reset_index(drop=True)
            gdf.to_parquet(geometry_cache, index=False)
            print(f"Saved geometry cache: {geometry_cache.name}")
            return gdf
        """
    ),
    md(
        """
        ## Step 1: Load Parcel Data

        Cleveland parcel data comes from the Cuyahoga County `MyPlace` ArcGIS REST service:

        - Base service: `https://gis.cuyahogacounty.us/server/rest/services/MyPLACE/Parcels_WMA_GJOIN_WGS84/MapServer`
        - Parcel layer: `2`
        - Geographic filter: `par_city = 'CLEVELAND'`

        This is a county-wide dataset, so Cleveland parcels are filtered from the county service. Pagination is required. The main parcel table already includes gross values, taxable values, exemptions, and abatements. The Cleveland city levy rate comes from Cuyahoga County's certified effective-rate table and is constant at `12.7` mills across Cleveland tax districts `740`, `750`, and `760`.
        """
    ),
    code(
        """
        parcel_attrs = load_attrs()
        parcel_geometry = load_geometry()

        gdf = parcel_geometry.merge(parcel_attrs, on=["objectid", "parcel_id"], how="inner")
        gdf = gdf.drop_duplicates(subset=["objectid"]).sort_values("objectid").reset_index(drop=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")

        print(gdf.shape)
        display(gdf.head(3))
        """
    ),
    code(
        """
        numeric_cols = [
            "certified_tax_land",
            "certified_tax_building",
            "certified_tax_total",
            "certified_exempt_land",
            "certified_exempt_building",
            "certified_exempt_total",
            "certified_abated_land",
            "certified_abated_building",
            "certified_abated_total",
            "gross_certified_land",
            "gross_certified_building",
            "gross_certified_total",
            "res_bldg_count",
            "com_bldg_count",
            "com_living_units",
            "total_res_liv_area",
            "total_com_use_area",
            "total_square_ft",
            "total_acreage",
        ]

        for col in numeric_cols:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0)

        gdf["existing_relief_total"] = gdf["certified_exempt_total"] + gdf["certified_abated_total"]
        gdf["existing_relief_land"] = gdf["certified_exempt_land"] + gdf["certified_abated_land"]
        gdf["existing_relief_building"] = gdf["certified_exempt_building"] + gdf["certified_abated_building"]
        gdf["existing_credit_amount"] = 0.0
        gdf["existing_credit_rate"] = 0.0
        gdf["full_exmp"] = (
            (gdf["certified_tax_total"] <= 0)
            | (gdf["existing_relief_total"] >= gdf["gross_certified_total"])
        ).astype(int)

        print("Parcel count:", len(gdf))
        print("Full exemption count:", int(gdf["full_exmp"].sum()))
        print("Distinct tax districts:", sorted(gdf["tax_district"].dropna().astype(str).unique().tolist()))
        print("Top use codes:")
        display(gdf["tax_luc_description"].value_counts(dropna=False).head(40))
        """
    ),
    md(
        """
        ## Step 2: Prepare Cleveland Parcels for Modeling

        Key Cleveland column mapping from the guide:

        - Land value: `gross_certified_land`
        - Improvement value: `gross_certified_building`
        - Total gross value: `gross_certified_total`
        - Taxable value after relief: `certified_tax_total`
        - Parcel id: `parcel_id`
        - Owner: `parcel_owner`
        - Neighborhood proxy: `neighborhood_code`
        - Use code: `tax_luc_description`

        Separate condo/unit aggregation does not appear necessary here. `condo_complex_id` exists, but only a tiny number of Cleveland records populate it and the parcel table does not expose a clear master-parcel key for a reliable condo collapse.
        """
    ),
    code(
        """
        # Cleveland land-use mapping into the common property categories used elsewhere in the repo.
        CLEVELAND_CATEGORY_MAP = {
            "1-FAMILY PLATTED LOT": "Single Family Residential",
            "ONE FAMILY LIHTC": "Single Family Residential",
            "2-FAMILY PLATTED LOT": "Small Multi-Family (2-4 units)",
            "3-FAMILY PLATTED LOT": "Small Multi-Family (2-4 units)",
            "4- 6 UNIT APARTMENTS": "Small Multi-Family (2-4 units)",
            "TWO FAMILY LIHTC": "Small Multi-Family (2-4 units)",
            "THREE FAMILY LIHTC": "Small Multi-Family (2-4 units)",
            "ROW HOUSING": "Small Multi-Family (2-4 units)",
            "WALK-UP APTS 7-19 U": "Large Multi-Family (5+ units)",
            "WALK-UP APTS 20-39 U": "Large Multi-Family (5+ units)",
            "WALK-UP APTS 40+ U": "Large Multi-Family (5+ units)",
            "ELEVATOR APTS 7-19 U": "Large Multi-Family (5+ units)",
            "ELEVATOR APTS 20-39U": "Large Multi-Family (5+ units)",
            "ELEVATOR APTS 40+ U": "Large Multi-Family (5+ units)",
            "GARDEN APTS 20-39 U": "Large Multi-Family (5+ units)",
            "GARDEN APTS 40+ U": "Large Multi-Family (5+ units)",
            "SUBSIDIZED HOUSING": "Large Multi-Family (5+ units)",
            "RES VACANT LAND": "Vacant Land",
            "COMMERCIAL VAC LAND": "Vacant Land",
            "VAC INDUSTRIAL LAND": "Vacant Land",
            "VACANT AG LAND-CAUV": "Vacant Land",
            "ASSOCIATD PARKNG LOT": "Transportation - Parking",
            "COMM PARKING LOT": "Transportation - Parking",
            "COMM PARKING GARAGE": "Transportation - Parking",
            "DETACHD STORE<7500SF": "Commercial",
            "STORE W/ WALKUP APTS": "Commercial",
            "STORE W/ WALKUP OFFC": "Commercial",
            "OTHER COMMERCIAL NEC": "Commercial",
            "SMALL SHOPS": "Commercial",
            "1-UNIT WHSE <75000SF": "Commercial",
            "1-UNIT WHSE >75000SF": "Commercial",
            "COMM WHSE LOFT-TYPE": "Commercial",
            "MULTI-TENANT WHSE": "Commercial",
            "DISTRIBUTION WHSE": "Commercial",
            "COMM TRUCK TERMINAL": "Commercial",
            "MINI-STORAGE WHSE": "Commercial",
            "BLDG MATERIAL STGE": "Commercial",
            "AUTO REPAIR GARAGE": "Commercial",
            "AUTO SALES & SERVICE": "Commercial",
            "TRUCK SALES & SVC": "Commercial",
            "USED CAR SALES": "Commercial",
            "FRANCHISE AUTO SVC": "Commercial",
            "SELF-SVC CAR WASH": "Commercial",
            "FS DRIVETHRU CARWASH": "Commercial",
            "GAS STATION W/ KIOSK": "Commercial",
            "FULL SVC GAS STATION": "Commercial",
            "CAFETERIA": "Commercial",
            "NIGHTCLUB": "Commercial",
            "NEIGHBORHOOD TAVERN": "Commercial",
            "FRANCHISE FD COUNTER": "Commercial",
            "FRANCHISE FD SITDOWN": "Commercial",
            "SUPERMARKET": "Commercial",
            "DISCNT/JR DEPT STORE": "Commercial",
            "GNRL RETAIL+ 7500 SQ": "Commercial",
            "STRIPCNTR 4+U>7500SF": "Commercial",
            "COMMUNITY SHOP CNTR": "Commercial",
            "OTHER RETAIL NEC": "Commercial",
            "FURNITURE MART": "Commercial",
            "HOME GARDEN CENTER": "Commercial",
            "HOME IMPRVMNT CENTER": "Commercial",
            "ICE CREAM STAND": "Commercial",
            "FULL SERVICE BANK": "Commercial",
            "SAVINGS AND LOAN": "Commercial",
            "POST OFFICE": "Commercial",
            "1-2 STORY OFFCE BLDG": "Commercial",
            "ELEVATOR OFFCE >2 ST": "Commercial",
            "WALKUP OFFICE >2 ST": "Commercial",
            "MED CLINIC/ OFFICES": "Commercial",
            "ANIMAL CLINIC/ HOSP": "Commercial",
            "OFFICE CONDO": "Commercial",
            "FUNERAL HOME": "Commercial",
            "LODGE HALL": "Commercial",
            "SPORT/ PUBLC ASSMBLY": "Commercial",
            "THEATRE": "Commercial",
            "CULTRL/NATURE EXHIBT": "Commercial",
            "MINATURE GOLF/DR RNG": "Commercial",
            "MARINE SVC FACILITY": "Commercial",
            "HOTELS": "Commercial",
            "MOTELS": "Commercial",
            "LIGHT MFG / ASSEMBLY": "Industrial",
            "MEDIUM MFG/ ASSEMBLY": "Industrial",
            "HEAVY MFG/ FOUNDRY": "Industrial",
            "FOOD/DRINK PROC/STGE": "Industrial",
            "SALVAGE/ SCRAP YARD": "Industrial",
            "M & E YARD STGE": "Industrial",
            "MATERIAL YARD STGE": "Industrial",
            "BILLBOARD SITE(S)": "Industrial",
            "BULK OIL STGE": "Industrial",
            "CONTRACT/ CONST SVCS": "Industrial",
            "COMMUNICATION FAC.": "Industrial",
            "TRANSPORTATION FAC.": "Industrial",
            "UTILITY SERVICE FAC.": "Industrial",
            "OTHER INDUSTRIAL NEC": "Industrial",
            "INDUSTRIAL COMMON AR": "Industrial",
            "R & D FACILITY": "Industrial",
            "LAND FILL": "Industrial",
            "MINES AND QUARRIES": "Industrial",
            "GRAIN ELEVATORS": "Industrial",
            "OTHER RES PLATTED": "Other Residential",
            "COMMON AREA PLATTED": "Other Residential",
            "LISTED WITH": "Other Residential",
            "MOBILE HOME PARK": "Other Residential",
            "OTHER COMM HSNG NEC": "Other Residential",
            "DORMITORY": "Other Residential",
            "NURSING HOME": "Other Residential",
            "CONVALESCENT HOME": "Other Residential",
            "HOSPITAL": "Other",
            "RR-USED IN OPERATION": "Other",
            "COM COMMON AREA": "Other",
            "COMMERCIAL CONDO": "Other",
            "FRUIT/NUT FARM-CAUV": "Agricultural",
            "VEGGIE FARM - CAUV": "Agricultural",
            "VEGETABLE FARM": "Agricultural",
            "GREENHOUSE": "Agricultural",
        }

        gdf["PROPERTY_CATEGORY"] = gdf["tax_luc_description"].map(CLEVELAND_CATEGORY_MAP).fillna("Other")
        gdf.loc[gdf["gross_certified_building"] <= 0, "PROPERTY_CATEGORY"] = "Vacant Land"

        print("Property category counts:")
        display(gdf["PROPERTY_CATEGORY"].value_counts())

        print("Codes still mapped to Other:")
        display(gdf.loc[gdf["PROPERTY_CATEGORY"] == "Other", "tax_luc_description"].value_counts(dropna=False))
        """
    ),
    md(
        """
        ## Step 3: Recreate Current Cleveland City Taxes

        This notebook models the **Cleveland city levy only**, not the full county / school / library tax stack.

        The city levy is sourced from Cuyahoga County's certified effective-rate table. The `CLEVELAND CITY` subtotal is `12.7` mills for the Cleveland-related tax districts that appear in the parcel data, so a single city millage can be applied to all Cleveland parcels in scope.

        The current-tax reconstruction now follows the policy order explicitly:

        1. Start from the already certified taxable land and building values.
        2. Apply the city levy millage.
        3. Apply any parcel-level credits after tax is computed.

        The parcel layer exposes exemptions and abatements, but it does **not** expose parcel-level rollback / credit amounts, so the Cleveland model currently sets credits to zero unless a supplemental source is added later.
        """
    ),
    code(
        """
        rate_params = {
            "f": "json",
            "where": "districtnum IN ('740','750','760') AND fillerfundname = 'CLEVELAND CITY'",
            "outFields": "districtnum,districtname,fillerfundname,rollbackidentifier,other_effective_rate,resag_effective_rate,totaltaxrate",
            "returnGeometry": "false",
        }
        rate_rows = requests.get(rate_query_url, params=rate_params, timeout=60).json()["features"]
        rate_df = pd.DataFrame([row["attributes"] for row in rate_rows])
        city_rate_df = rate_df[rate_df["rollbackidentifier"] == "SUB TOTAL"].copy()
        city_millage = float(city_rate_df["other_effective_rate"].iloc[0])

        display(city_rate_df[["districtnum", "districtname", "other_effective_rate", "resag_effective_rate"]])
        print(f"Using Cleveland city levy millage: {city_millage:.2f}")
        """
    ),
    code(
        """
        # Calculate current Cleveland city tax from the certified taxable components, then apply credits.
        gdf["millage_rate"] = city_millage

        current_revenue, _, gdf = calculate_current_tax(
            df=gdf,
            tax_value_col="certified_tax_total",
            millage_rate_col="millage_rate",
            land_value_col="certified_tax_land",
            improvement_value_col="certified_tax_building",
            credit_col="existing_credit_amount",
            credit_rate_col="existing_credit_rate",
        )

        identity_revenue = gdf["certified_tax_total"].clip(lower=0).sum() * city_millage / 1000.0
        print(f"Modeled current city revenue: ${current_revenue:,.0f}")
        print(f"Identity check using certified_tax_total: ${identity_revenue:,.0f}")
        print(f"Difference vs identity check: {(current_revenue / identity_revenue - 1) * 100:.4f}%")
        print("Parcel-level credits applied in current model: $0 (no credit fields in source parcel table)")
        """
    ),
    code(
        """
        # Remove fully exempt parcels from the modeling set.
        df = gdf[gdf["full_exmp"] != 1].copy()
        print(f"Removed {len(gdf) - len(df):,} fully exempt parcels")
        print(f"Remaining model parcels: {len(df):,}")
        """
    ),
    md(
        """
        ## Step 4: Modeling the Split-Rate Land Value Tax

        Main Cleveland scenarios:

        - `2:1` split-rate LVT
        - `4:1` split-rate LVT
        - `100%` building exemption benchmark
        """
    ),
    code(
        """
        def run_split_rate_scenario(df_input, ratio):
            land_millage, improvement_millage, new_revenue, modeled = model_split_rate_tax(
                df=df_input,
                land_value_col="gross_certified_land",
                improvement_value_col="gross_certified_building",
                current_revenue=current_revenue,
                land_improvement_ratio=ratio,
                exemption_col="existing_relief_total",
                exemption_flag_col="full_exmp",
                credit_col="existing_credit_amount",
                credit_rate_col="existing_credit_rate",
            )
            sf_mask = modeled["PROPERTY_CATEGORY"] == "Single Family Residential"
            return {
                "scenario": f"Split-rate {ratio}:1",
                "land_millage": land_millage,
                "improvement_millage": improvement_millage,
                "new_revenue": new_revenue,
                "median_sf_pct_change": modeled.loc[sf_mask, "tax_change_pct"].median(),
                "mean_city_pct_change": modeled["tax_change_pct"].mean(),
                "df": modeled,
            }


        def run_full_building_exemption(df_input):
            modeled = df_input.copy()
            gross_land = modeled["gross_certified_land"].astype(float)
            gross_improvement = modeled["gross_certified_building"].astype(float)
            relief = modeled["existing_relief_total"].astype(float).clip(lower=0)

            taxable_improvement = (gross_improvement * 0.0).clip(lower=0)
            remaining_relief = relief.copy()
            taxable_land = (gross_land - remaining_relief).clip(lower=0)
            modeled["new_taxable_base"] = taxable_land + taxable_improvement

            single_millage = (current_revenue * 1000.0) / modeled["new_taxable_base"].sum()
            modeled["new_tax_before_credits"] = (modeled["new_taxable_base"] * single_millage / 1000.0).clip(lower=0)
            modeled["new_credit_amount"] = np.minimum(
                modeled["new_tax_before_credits"],
                modeled["existing_credit_amount"].astype(float).clip(lower=0)
                + modeled["new_tax_before_credits"] * modeled["existing_credit_rate"].astype(float).clip(lower=0, upper=1),
            )
            modeled["new_tax"] = (modeled["new_tax_before_credits"] - modeled["new_credit_amount"]).clip(lower=0)
            modeled["tax_change"] = modeled["new_tax"] - modeled["current_tax"]
            modeled["tax_change_pct"] = np.where(
                modeled["current_tax"] > 0,
                modeled["tax_change"] / modeled["current_tax"] * 100.0,
                0.0,
            )

            sf_mask = modeled["PROPERTY_CATEGORY"] == "Single Family Residential"
            return {
                "scenario": "100% building exemption",
                "land_millage": single_millage,
                "improvement_millage": 0.0,
                "new_revenue": modeled["new_tax"].sum(),
                "median_sf_pct_change": modeled.loc[sf_mask, "tax_change_pct"].median(),
                "mean_city_pct_change": modeled["tax_change_pct"].mean(),
                "df": modeled,
            }


        scenarios = [
            run_split_rate_scenario(df, 2),
            run_split_rate_scenario(df, 4),
            run_full_building_exemption(df),
        ]

        scenario_summary = pd.DataFrame(
            [
                {
                    "scenario": s["scenario"],
                    "land_millage": s["land_millage"],
                    "improvement_millage": s["improvement_millage"],
                    "new_revenue": s["new_revenue"],
                    "median_sf_pct_change": s["median_sf_pct_change"],
                    "mean_city_pct_change": s["mean_city_pct_change"],
                }
                for s in scenarios
            ]
        )

        display(scenario_summary)
        """
    ),
    code(
        """
        cleveland_4to1 = next(s for s in scenarios if s["scenario"] == "Split-rate 4:1")["df"].copy()

        category_summary = calculate_category_tax_summary(
            df=cleveland_4to1,
            category_col="PROPERTY_CATEGORY",
            current_tax_col="current_tax",
            new_tax_col="new_tax",
            pct_threshold=10.0,
        )

        print_category_tax_summary(
            summary_df=category_summary,
            title="4:1 Split-Rate Tax Impact by Property Category - Cleveland, OH",
            pct_threshold=10.0,
        )

        display(category_summary)
        """
    ),
    md(
        """
        ## Step 5: Property Category Impact Charts

        This chart is intentionally formatted to match the horizontal property-category impact bars used in Syracuse / Spokane-style notebook cells.
        """
    ),
    code(
        """
        # Property category impact chart (Spokane / Syracuse style, sorted by median tax change percent)
        filtered = category_summary[category_summary["median_tax_change_pct"] != 0].copy()
        filtered = filtered[filtered["property_count"] > 0]

        categories = filtered["PROPERTY_CATEGORY"].tolist()
        counts = filtered["property_count"].tolist()
        median_pct_change = filtered["median_tax_change_pct"].tolist()
        median_dollar_change = filtered["median_tax_change"].tolist()
        total_tax_change = filtered["total_tax_change_dollars"].tolist()

        sorted_idx = np.argsort(median_pct_change)
        categories = [categories[i] for i in sorted_idx]
        counts = [counts[i] for i in sorted_idx]
        median_pct_change = [median_pct_change[i] for i in sorted_idx]
        median_dollar_change = [median_dollar_change[i] for i in sorted_idx]
        total_tax_change = [total_tax_change[i] for i in sorted_idx]

        bar_colors = ["#8B0000" if val > 0 else "#228B22" for val in median_pct_change]

        bar_height = 0.75
        fig_height = len(categories) * 0.8 + 1.2
        right_col_pad = 120
        fig, ax = plt.subplots(figsize=(17, fig_height))
        y = np.arange(len(categories))

        ax.barh(
            y,
            median_pct_change,
            color=bar_colors,
            edgecolor="none",
            height=bar_height,
            alpha=0.92,
            linewidth=0,
            zorder=2,
        )

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

        cat_offset = 0.18
        med_offset = -0.03
        count_offset = -0.23
        max_abs = max(abs(min(median_pct_change)), abs(max(median_pct_change)))
        right_col_x = max_abs + right_col_pad

        ax.text(
            right_col_x,
            len(categories) - 0.5,
            "Net Change",
            va="bottom",
            ha="left",
            fontsize=15,
            fontweight="bold",
            color="black",
        )

        for i, (cat, val, count, med_dol, tot_change) in enumerate(
            zip(categories, median_pct_change, counts, median_dollar_change, total_tax_change)
        ):
            med_dol_str = f"${med_dol:,.0f}" if med_dol >= 0 else f"-${abs(med_dol):,.0f}"
            pct_str = f"{val:+.1f}%"
            median_combo = f"Median: {med_dol_str}, {pct_str}"

            if val < 0:
                xpos = val - 2.5
                ha = "right"
            else:
                xpos = val + 2.5
                ha = "left"

            ax.text(xpos, y[i] + cat_offset, cat, va="center", ha=ha, fontsize=14, fontweight="bold", color="#222")
            ax.text(xpos, y[i] + med_offset, median_combo, va="center", ha=ha, fontsize=12, fontweight="bold", color="black")
            ax.text(xpos, y[i] + count_offset, f"{count:,} parcels", va="center", ha=ha, fontsize=11, fontweight="bold", color="#888")

            tot_change_str = f"${tot_change:,.0f}" if tot_change >= 0 else f"-${abs(tot_change):,.0f}"
            ax.text(
                right_col_x,
                y[i],
                tot_change_str,
                va="center",
                ha="left",
                fontsize=13,
                fontweight="bold",
                color="black",
            )

        ax.set_xlim(-right_col_x, right_col_x + 60)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_title("4:1 Split-Rate Tax Impact by Property Category - Cleveland, OH", fontsize=16, fontweight="bold", pad=18)

        plt.tight_layout()
        plt.show()
        """
    ),
    code(
        """
        vacant_results = analyze_vacant_land(
            df=cleveland_4to1,
            land_value_col="gross_certified_land",
            improvement_value_col="gross_certified_building",
            property_type_col="PROPERTY_CATEGORY",
            vacant_identifier="Vacant Land",
            neighborhood_col="neighborhood_code",
            owner_col="parcel_owner",
            exemption_col="existing_relief_total",
            exemption_flag_col="full_exmp",
        )
        print_vacant_land_summary(vacant_results)

        parking_results = analyze_parking_lots(
            df=cleveland_4to1,
            land_value_col="gross_certified_land",
            improvement_value_col="gross_certified_building",
            property_type_col="PROPERTY_CATEGORY",
            parking_identifier="Transportation - Parking",
            exemption_col="existing_relief_total",
            exemption_flag_col="full_exmp",
        )
        print_parking_analysis_summary(parking_results)
        """
    ),
    md(
        """
        ## Step 6: Adding Geographic Context

        Census demographics are joined at the census block-group level using the county FIPS for Cuyahoga County, Ohio:

        - County FIPS: `39035`
        - ACS year: `2022`

        The notebook loads the Census API key from `.env` and then spatially joins Cleveland parcels to block groups using parcel centroids, matching the repo's existing helper logic.
        """
    ),
    code(
        """
        census_api_key = os.getenv("CENSUS_API_KEY")
        print("CENSUS_API_KEY loaded:", bool(census_api_key))

        census_data, census_boundaries = get_census_data_with_boundaries(
            fips_code="39035",
            year=2022,
            api_key=census_api_key,
        )

        if census_boundaries.crs is None:
            census_boundaries = census_boundaries.set_crs(epsg=4326)

        if cleveland_4to1.crs != census_boundaries.crs:
            cleveland_4to1 = cleveland_4to1.to_crs(census_boundaries.crs)

        df_geo = match_to_census_blockgroups(
            gdf=cleveland_4to1,
            census_gdf=census_boundaries,
        )

        print(f"Number of parcels with geometry: {len(df_geo):,}")
        print(f"Number of census block groups: {len(census_boundaries):,}")
        print("Key demographic columns present:")
        display([col for col in ["std_geoid", "median_income", "minority_pct", "black_pct", "total_pop"] if col in df_geo.columns])
        """
    ),
    md(
        """
        ## Step 7: Demographic and Equity Analysis

        These cells mirror the census-progressivity bar charts used in Syracuse and related notebooks: one set for neighborhood income quintiles and another for neighborhood minority-share quintiles.
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
        def create_quintile_summary(df_input, value_col, labels=None):
            if labels is None:
                labels = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]

            work = df_input[(df_input[value_col].notna())].copy()
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
            fig, ax = plt.subplots(figsize=(10, 6))

            vals = summary_df["median_tax_change_pct"].astype(float)
            labels = summary_df["quintile"]

            colors = sns.color_palette("Greens", n_colors=len(vals))
            color_map = [colors[i] for i in np.argsort(np.argsort(-vals))]

            bars = ax.bar(
                labels,
                np.abs(vals),
                color=color_map,
                edgecolor="black",
                width=0.7,
            )

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
        # Excluding vacant land, all remaining property categories.
        non_vacant_gdf = df_geo[df_geo["PROPERTY_CATEGORY"] != "Vacant Land"].copy()

        print("Tax impact by income quintile (excluding vacant land):")
        non_vacant_income_quintile_summary = create_quintile_summary(non_vacant_gdf, "median_income")
        display(non_vacant_income_quintile_summary)

        plot_upside_down_quintile_bars(
            non_vacant_income_quintile_summary,
            "Median Tax Change by Neighborhood Median Income (Excl. Vacant Land)",
        )
        """
    ),
    code(
        """
        print("Tax impact by minority-share quintile (excluding vacant land):")
        non_vacant_minority_quintile_summary = create_quintile_summary(non_vacant_gdf, "minority_pct")
        display(non_vacant_minority_quintile_summary)

        plot_upside_down_quintile_bars(
            non_vacant_minority_quintile_summary,
            "Median Tax Change by Minority Percentage Quintile (Excl. Vacant Land)",
        )
        """
    ),
    md(
        """
        ## Step 8: Single-Family Progressivity Analysis

        This section reruns the progressivity lookups for **single-family housing only**, while also excluding vacant land. Since the subset is already limited to `Single Family Residential`, the vacant-land exclusion is satisfied by construction and kept explicit in the code.
        """
    ),
    code(
        """
        df_single_family = df_geo[
            (df_geo["PROPERTY_CATEGORY"] == "Single Family Residential")
            & (df_geo["PROPERTY_CATEGORY"] != "Vacant Land")
        ].copy()

        print(f"Single-family parcels in demographic analysis: {len(df_single_family):,}")

        non_vacant_income_quintile_summary_sf = create_quintile_summary(df_single_family, "median_income")
        non_vacant_minority_quintile_summary_sf = create_quintile_summary(df_single_family, "minority_pct")

        print("\\nSingle-family tax impact by income quintile:")
        display(non_vacant_income_quintile_summary_sf)

        print("\\nSingle-family tax impact by minority percentage quintile:")
        display(non_vacant_minority_quintile_summary_sf)
        """
    ),
    code(
        """
        plot_upside_down_quintile_bars(
            non_vacant_income_quintile_summary_sf,
            "Median Tax Change by Neighborhood Median Income (Excl. Vacant Land, Single Family Only)",
        )

        plot_upside_down_quintile_bars(
            non_vacant_minority_quintile_summary_sf,
            "Median Tax Change by Minority Percentage Quintile (Excl. Vacant Land, Single Family Only)",
        )
        """
    ),
    md(
        """
        ## Step 9: All-Residential Progressivity Analysis

        This section repeats the same progressivity analysis for the broader **residential** subset: single-family, small multi-family, and large multi-family parcels, while still excluding vacant land.
        """
    ),
    code(
        """
        residential_categories = [
            "Single Family Residential",
            "Small Multi-Family (2-4 units)",
            "Large Multi-Family (5+ units)",
        ]

        df_all_residential = df_geo[
            df_geo["PROPERTY_CATEGORY"].isin(residential_categories)
            & (df_geo["PROPERTY_CATEGORY"] != "Vacant Land")
        ].copy()

        print(f"All-residential parcels in demographic analysis: {len(df_all_residential):,}")

        non_vacant_income_quintile_summary_res = create_quintile_summary(df_all_residential, "median_income")
        non_vacant_minority_quintile_summary_res = create_quintile_summary(df_all_residential, "minority_pct")

        print("\\nAll-residential tax impact by income quintile:")
        display(non_vacant_income_quintile_summary_res)

        print("\\nAll-residential tax impact by minority percentage quintile:")
        display(non_vacant_minority_quintile_summary_res)
        """
    ),
    code(
        """
        plot_upside_down_quintile_bars(
            non_vacant_income_quintile_summary_res,
            "Median Tax Change by Neighborhood Median Income (Excl. Vacant Land, All Residential)",
        )

        plot_upside_down_quintile_bars(
            non_vacant_minority_quintile_summary_res,
            "Median Tax Change by Minority Percentage Quintile (Excl. Vacant Land, All Residential)",
        )
        """
    ),
    code(
        """
        modeled_output_path = data_dir / f"cleveland_modeled_4to1_{datetime.now().strftime('%Y%m%d')}.parquet"
        cleveland_4to1.to_parquet(modeled_output_path, index=False)
        print(f"Saved modeled 4:1 output to {modeled_output_path}")
        modeled_output_path
        """
    ),
]

nb["metadata"]["kernelspec"] = {
    "display_name": "CLE New Environment",
    "language": "python",
    "name": "cle-venv-new",
}
nb["metadata"]["language_info"] = {"name": "python", "version": "3.x"}

NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, NOTEBOOK_PATH)
print(f"Wrote {NOTEBOOK_PATH}")
