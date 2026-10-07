"""
Builds data/beef_production_ranks.csv for the bump chart.
Run from the repo root:  python scripts/prepare_production_ranks.py

Input: data/raw/FAOSTAT_data_en_10-2-2026.csv (FAOSTAT QCL, meat of cattle, production, 2005-2024)
Steps:
1. Drop FAOSTAT's 'China' total (code 159) so China isn't counted twice (see prepare_world_production.py).
2. Rank every country by production in each year (1 = largest).
3. Keep the 13 countries that were in the top 10 in at least one year.
"""
import pandas as pd

q = pd.read_csv("data/raw/FAOSTAT_data_en_10-2-2026.csv", dtype={"Area Code (M49)": str})
q = q[q["Area Code (M49)"] != "159"].dropna(subset=["Value"])
q["rank"] = q.groupby("Year")["Value"].rank(ascending=False, method="min").astype(int)
ever_top10 = q.loc[q["rank"] <= 10, "Area"].unique()
short = {"United States of America": "United States", "China, mainland": "China",
         "Russian Federation": "Russia", "Türkiye": "Turkey"}
out = q[q["Area"].isin(ever_top10)].copy()
out["country"] = out["Area"].replace(short)
out = out.rename(columns={"Year": "year", "Value": "tonnes"})
out[["country", "year", "rank", "tonnes"]].sort_values(["country", "year"]).to_csv(
    "data/beef_production_ranks.csv", index=False)
print(out.pivot(index="country", columns="year", values="rank")[[2005, 2015, 2020, 2021, 2022, 2024]])
