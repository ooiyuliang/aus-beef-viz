"""
Builds two CSVs from ABS 7215.0 Livestock Products, Table 3
('Livestock slaughtered - cattle (excluding calves): all series', thousand head).
Run from the repo root:  python scripts/prepare_slaughter.py

1. data/cattle_slaughter_quarterly.csv  (heatmap)
   - Uses the 'Total (State)' column, Original series (not seasonally adjusted, so the
     normal ups and downs within each year are kept).
   - Keeps quarters from March 2005 to the latest available.
2. data/cattle_cycle_2005_2025.csv  (connected scatterplot)
   - Adds up the four quarters of each financial year (Sep, Dec, Mar, Jun), so that a year
     ending 30 June matches the herd count taken on 30 June (from beef_herd_2005_2025.csv).
"""
import pandas as pd

raw = pd.read_excel("data/raw/ABS_7215_livestock_slaughtered_cattle.xlsx", sheet_name="Data1", header=None)
col = next(c for c in raw.columns
           if "Total (State)" in str(raw.iloc[0, c]) and raw.iloc[2, c] == "Original")
q = raw.iloc[10:, [0, col]].dropna()
q.columns = ["date", "slaughter_000"]
q["date"] = pd.to_datetime(q["date"])
q["slaughter_000"] = q["slaughter_000"].astype(float)
q["year"] = q["date"].dt.year
q["quarter"] = q["date"].dt.month.map({3: "Jan–Mar", 6: "Apr–Jun", 9: "Jul–Sep", 12: "Oct–Dec"})

heat = q[q["year"] >= 2005].copy()
heat["date"] = heat["date"].dt.strftime("%Y-%m")
heat[["year", "quarter", "date", "slaughter_000"]].to_csv("data/cattle_slaughter_quarterly.csv", index=False)

q["fy_end"] = q["year"] + (q["date"].dt.month >= 9).astype(int)      # Sep/Dec belong to the next 30 June
fy = q.groupby("fy_end").agg(slaughter_000=("slaughter_000", "sum"), n=("slaughter_000", "size")).reset_index()
fy = fy[(fy["n"] == 4) & fy["fy_end"].between(2005, 2025)]
herd = pd.read_csv("data/beef_herd_2005_2025.csv").query("code == 'AUS'")[["year", "beef_cattle"]]
cyc = herd.merge(fy.rename(columns={"fy_end": "year"}), on="year")
cyc["herd_m"] = (cyc["beef_cattle"] / 1e6).round(3)
cyc["slaughter_m"] = (cyc["slaughter_000"] / 1000).round(3)
cyc[["year", "herd_m", "slaughter_m"]].to_csv("data/cattle_cycle_2005_2025.csv", index=False)

cal = q.groupby("year")["slaughter_000"].sum()
print("Latest quarter:", q["date"].max().date(), "| calendar 2014:", round(cal[2014]), "| 2025:", round(cal[2025]))
print(cyc.to_string(index=False))
