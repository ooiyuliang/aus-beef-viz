"""
Builds data/beef_production_world.csv for the world proportional symbol map and the bump chart.
Run from the repo root:  python scripts/prepare_world_production.py

Inputs:
- data/raw/FAOSTAT_data_en_10-2-2026.csv  (FAOSTAT QCL: 'Meat of cattle with the bone, fresh or chilled',
  element 'Production', tonnes, all countries, 2005-2024)
- data/raw/world_110m_country_points.csv  (one point inside each country of world-110m.json, made with
  mapshaper: -target countries -points inner -each 'lon=this.x, lat=this.y')

Steps:
1. Drop FAOSTAT's 'China' row (code 159). It is a total of mainland China, Hong Kong, Macao and Taiwan,
   which also appear as separate rows, so keeping it would count China twice.
2. Keep the years 2005, 2015 and 2024 and rank countries by production within each year.
3. Join each country to its map point using the UN M49 code, which matches the world map's id.
4. Shorten a few long official names for labels (e.g. 'United States of America' -> 'United States').
"""
import pandas as pd

fao = pd.read_csv("data/raw/FAOSTAT_data_en_10-2-2026.csv", dtype={"Area Code (M49)": str})
fao = fao[fao["Area Code (M49)"] != "159"]                       # step 1
fao["m49"] = fao["Area Code (M49)"].astype(int)
fao = fao[fao["Year"].isin([2005, 2015, 2024])].dropna(subset=["Value"])   # step 2
fao["rank"] = fao.groupby("Year")["Value"].rank(ascending=False, method="min").astype(int)

pts = pd.read_csv("data/raw/world_110m_country_points.csv").rename(columns={"FID": "m49"})
df = fao.merge(pts, on="m49", how="inner")                       # step 3

short = {"United States of America": "United States", "China, mainland": "China",
         "Russian Federation": "Russia", "Iran (Islamic Republic of)": "Iran",
         "Türkiye": "Turkey", "Viet Nam": "Vietnam", "Republic of Korea": "South Korea",
         "Bolivia (Plurinational State of)": "Bolivia", "Venezuela (Bolivarian Republic of)": "Venezuela",
         "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
         "United Republic of Tanzania": "Tanzania", "China, Taiwan Province of": "Taiwan"}
df["country"] = df["Area"].replace(short)                        # step 4
df = df.rename(columns={"Year": "year", "Value": "tonnes"})
df["lon"] = df["lon"].round(2)
df["lat"] = df["lat"].round(2)
df[["country", "m49", "year", "tonnes", "rank", "lon", "lat"]].sort_values(["year", "rank"]).to_csv(
    "data/beef_production_world.csv", index=False)

missing = sorted(set(fao["Area"]) - set(df["Area"]))
print("Countries on the map:", df[df.year == 2024].shape[0], "| not on the 110m map (too small):", len(missing))
print(df[df.year == 2024].head(10)[["rank", "country", "tonnes"]].to_string(index=False))
print(df[df.country == "Malaysia"][["year", "rank", "tonnes"]].to_string(index=False))
