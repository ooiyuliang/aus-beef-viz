"""
Turns the DAFF '57 Destination Report' (Calendar YTD, December 2025) into a small CSV
for the flow map. Run from the repo root:  python scripts/prepare_exports.py data/raw/2512_c57dest.xlsx

Steps:
1. Read the 'Beef & Veal Total' column (tonnes shipped weight) for each destination row.
2. Drop regional subtotal rows (e.g. 'Total Asia') and grouped rows (e.g. 'Other Asia'),
   because they are not single countries and can't be placed on a map.
3. Combine rows that DAFF splits within one country:
   USA East + USA West + Hawaii -> United States; Canada East + West -> Canada;
   Dubai + Abu Dhabi -> United Arab Emirates.
4. Keep countries that received at least 5,000 tonnes, plus Malaysia (our audience).
5. Add each country's capital city coordinates (where the line ends on the map).
"""
import sys
import pandas as pd

src = sys.argv[1] if len(sys.argv) > 1 else "data/raw/2512_c57dest.xlsx"
raw = pd.read_excel(src, header=None)

# Find the header row and the beef column by name rather than by position
hdr = raw.index[raw[0].astype(str).str.strip() == "Destinations"][0]
cols = [str(c).strip() for c in raw.iloc[hdr]]
beef_col = cols.index("Beef & Veal Total")
df = raw.iloc[hdr + 1:, [0, beef_col]].copy()
df.columns = ["destination", "tonnes"]
df = df.dropna()
df["destination"] = df["destination"].astype(str).str.strip()
df["tonnes"] = pd.to_numeric(df["tonnes"])

national_total = float(df.loc[df["destination"] == "Total Aus", "tonnes"].iloc[0])

merge = {"USA East": "United States", "USA West": "United States", "Hawaii": "United States",
         "Canada East": "Canada", "Canada West": "Canada",
         "Dubai": "United Arab Emirates", "Abu Dhabi": "United Arab Emirates"}
df["country"] = df["destination"].replace(merge)

not_countries = ("Total", "Other", "All Other", "C I S", "East Europe", "Caribbean",
                 "Pacific Islands", "Ship Stores")
df = df[~df["country"].str.startswith(not_countries)]
by_country = df.groupby("country", as_index=False)["tonnes"].sum()
by_country["rank"] = by_country["tonnes"].rank(ascending=False, method="min").astype(int)
by_country["share"] = by_country["tonnes"] / national_total

# Capital city coordinates [longitude, latitude]
capitals = {
    "United States": (-77.04, 38.91), "China": (116.40, 39.90), "Japan": (139.69, 35.69),
    "South Korea": (126.98, 37.57), "Indonesia": (106.85, -6.21), "Canada": (-75.70, 45.42),
    "Taiwan": (121.56, 25.03), "Thailand": (100.50, 13.76), "Philippines": (120.98, 14.60),
    "United Kingdom": (-0.13, 51.51), "United Arab Emirates": (54.37, 24.45),
    "Saudi Arabia": (46.68, 24.71), "Malaysia": (101.69, 3.14), "New Zealand": (174.78, -41.29),
    "Hong Kong": (114.17, 22.32), "Singapore": (103.82, 1.35), "Netherlands": (4.90, 52.37),
}
keep = by_country[(by_country["tonnes"] >= 5000) | (by_country["country"] == "Malaysia")].copy()
missing = set(keep["country"]) - set(capitals)
assert not missing, f"Add coordinates for: {missing}"
keep["lon"] = keep["country"].map(lambda c: capitals[c][0])
keep["lat"] = keep["country"].map(lambda c: capitals[c][1])
keep["tonnes"] = keep["tonnes"].round(0).astype(int)
keep["share"] = keep["share"].round(4)
keep = keep.sort_values("tonnes", ascending=False)
keep[["country", "tonnes", "share", "rank", "lon", "lat"]].to_csv(
    "data/beef_exports_2025.csv", index=False)

print(f"Total Australian beef & veal exports 2025: {national_total:,.0f} t")
print(f"Countries mapped: {len(keep)}, covering {keep['tonnes'].sum() / national_total:.1%} of exports")
print(keep.to_string(index=False))
