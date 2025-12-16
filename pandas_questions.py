"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = "./data/"


def load_data():
    """Load data from the CSV files referendum/regions/departments."""
    referendum = pd.read_csv(f"{DATA_DIR}referendum.csv", sep=";")
    regions = pd.read_csv(f"{DATA_DIR}regions.csv", sep=",")
    departments = pd.read_csv(f"{DATA_DIR}departments.csv", sep=",")
    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    reg = regions.rename(
        columns={"code": "code_reg", "name": "name_reg"}
    ).copy()
    dep = departments.rename(
        columns={"code": "code_dep", "name": "name_dep"}
    ).copy()

    if "code_reg" not in dep.columns:
        for col in ["region_code", "reg_code", "region", "code_region"]:
            if col in dep.columns:
                dep = dep.rename(columns={col: "code_reg"})
                break

    reg["code_reg"] = reg["code_reg"].astype(str)
    dep["code_reg"] = dep["code_reg"].astype(str)
    dep["code_dep"] = dep["code_dep"].astype(str)

    merged = dep.merge(
        reg[["code_reg", "name_reg"]],
        on="code_reg",
        how="left",
    )
    return merged[["code_reg", "name_reg", "code_dep", "name_dep"]]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the french
    living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    ref = referendum.copy()
    areas = regions_and_departments.copy()

    ref["code_dep"] = ref["Department code"].astype(str).str.strip()
    areas["code_dep"] = areas["code_dep"].astype(str).str.strip()

    is_num_ref = ref["code_dep"].str.fullmatch(r"\d+")
    ref.loc[is_num_ref, "code_dep"] = (
        ref.loc[is_num_ref, "code_dep"].str.zfill(2)
    )

    is_num_areas = areas["code_dep"].str.fullmatch(r"\d+")
    areas.loc[is_num_areas, "code_dep"] = (
        areas.loc[is_num_areas, "code_dep"].str.zfill(2)
    )

    ref = ref[~ref["code_dep"].str.contains("Z", na=False)].copy()

    merged = ref.merge(areas, on="code_dep", how="left")
    merged = merged.dropna()
    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    df = referendum_and_areas.copy()

    cols = ["Registered", "Abstentions", "Null", "Choice A", "Choice B"]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    out = (
        df.groupby(["code_reg", "name_reg"], as_index=False)[cols]
        .sum()
        .set_index("code_reg")
    )
    return out[["name_reg"] + cols]


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use `GeoDataFrame.plot` to display the result map. The results should
      display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    geo = gpd.read_file(f"{DATA_DIR}regions.geojson")
    geo = geo.rename(columns={"code": "code_reg", "nom": "name_reg"})
    geo["code_reg"] = geo["code_reg"].astype(str)

    df = referendum_result_by_regions.reset_index()
    df["code_reg"] = df["code_reg"].astype(str)

    gdf = geo.merge(df, on="code_reg", how="left", suffixes=("_geo", "_data"))

    if "name_reg" not in gdf.columns:
        if "name_reg_geo" in gdf.columns:
            gdf["name_reg"] = gdf["name_reg_geo"]
        elif "name_reg_data" in gdf.columns:
            gdf["name_reg"] = gdf["name_reg_data"]

    expressed = gdf["Choice A"] + gdf["Choice B"]
    gdf["ratio"] = gdf["Choice A"] / expressed.replace(0, pd.NA)

    gdf.plot(column="ratio", legend=True)
    plt.title("Referendum results (Choice A / expressed ballots)")
    plt.axis("off")

    return gdf


if __name__ == "__main__":
    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(df_reg, df_dep)
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
