"""
Turns the ABS 'Cattle herd series 2005 to 2025' data cube into a tidy CSV.
Run from the repo root:  python scripts/prepare_herd.py

Steps:
1. Read 'Table 1' (experimental estimates, one consistent method for every year 2005-2025).
   Table 2 is skipped: it uses the older survey method and stops at 2022.
2. Keep only the 'Beef cattle - Total' rows (dairy cattle are excluded).
3. Reshape from wide (one column per year) to long (one row per region per year).
4. Financial years such as '2019-20' are counts at 30 June, so '2019-20' becomes 30 June 2020.
"""
import pandas as pd

raw = pd.read_excel("data/raw/AALDC_Cattle_herd_series_2005_to_2025.xlsx",
                    sheet_name="Table 1", header=None)
hdr = raw.index[raw[0].astype(str).str.strip() == "Region"][0]
raw.columns = [str(c).strip() for c in raw.iloc[hdr]]
df = raw.iloc[hdr + 1:]
df = df[df["Data item"].astype(str).str.startswith("Beef cattle - Total")]

year_cols = [c for c in df.columns if len(c) == 7 and c[4] == "-"]
long = df.melt(id_vars=["Region"], value_vars=year_cols,
               var_name="financial_year", value_name="beef_cattle")
long["year"] = long["financial_year"].str[:4].astype(int) + 1     # '2019-20' -> 2020
long["date"] = long["year"].astype(str) + "-06-30"
long["beef_cattle"] = long["beef_cattle"].astype(int)
codes = {"Australia": "AUS", "New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD",
         "South Australia": "SA", "Western Australia": "WA", "Tasmania": "TAS",
         "Northern Territory": "NT"}
long["code"] = long["Region"].map(codes)
long = long.rename(columns={"Region": "region"})
long[["region", "code", "financial_year", "year", "date", "beef_cattle"]].to_csv(
    "data/beef_herd_2005_2025.csv", index=False)

aus = long[long["code"] == "AUS"].set_index("year")["beef_cattle"]
print(long.shape, "rows")
print("Peak:", aus.idxmax(), f"{aus.max():,}", "| Low:", aus.idxmin(), f"{aus.min():,}")
