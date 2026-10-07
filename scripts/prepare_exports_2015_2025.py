"""
Builds data/beef_exports_2015_2025.csv for the slope chart.
Run from the repo root:  python scripts/prepare_exports_2015_2025.py

The DAFF 2015 report (1512_c57dest.doc) is a Word file, not a spreadsheet. Convert it first with
LibreOffice:  soffice --headless --convert-to html data/raw/1512_c57dest.doc --outdir data/raw

Steps:
1. 2015: read page 1 of the report (beef and veal). Each destination is followed by 14 numbers;
   the 13th is 'Total Beef & Veal' (tonnes shipped weight). Checked: Japan = 127,631 chilled
   + 157,592 frozen = 285,223 total.
2. 2025: read the 'Beef & Veal Total' column of 2512_c57dest.xlsx.
3. Use the same country names for both years (e.g. 'USA EC' + 'USA WC' + 'Hawaii' -> United States).
4. Keep the five largest 2025 markets plus Malaysia.
"""
import re
import pandas as pd
from bs4 import BeautifulSoup

NAMES = {"USA EC": "United States", "USA WC": "United States", "HAWAII": "United States",
         "USA East": "United States", "USA West": "United States", "Hawaii": "United States",
         "CHINA": "China", "JAPAN": "Japan", "SOUTH KOREA": "South Korea", "Korea": "South Korea",
         "INDONESIA": "Indonesia", "MALAYSIA": "Malaysia", "TOTAL AUS": "TOTAL", "Total Aus": "TOTAL"}
NAMES.update({c: c for c in ["China", "Japan", "South Korea", "Indonesia", "Malaysia"]})

# --- 2015 (Word report) ---
html = open("data/raw/1512_c57dest.html", encoding="latin-1").read()
text = BeautifulSoup(html, "html.parser").get_text("|", strip=True)
page1 = text.split("D.A.F.F")[0].split("Destinations|", 1)[1]
tokens = [re.sub(r"\s+", " ", t).strip() for t in page1.split("|")]
rows, i = [], 0
while i < len(tokens):
    if tokens[i].replace(",", "").isdigit():
        i += 1
        continue
    name, nums = tokens[i], tokens[i + 1:i + 15]
    if len(nums) < 14:          # end of the table
        break
    rows.append((name, int(nums[12])))
    i += 15
y2015 = pd.DataFrame(rows, columns=["destination", "tonnes"])
y2015["country"] = y2015["destination"].map(NAMES)
y2015 = y2015.dropna().groupby("country")["tonnes"].sum()

# --- 2025 (Excel report) ---
raw = pd.read_excel("data/raw/2512_c57dest.xlsx", header=None)
hdr = raw.index[raw[0].astype(str).str.strip() == "Destinations"][0]
cols = [str(c).strip() for c in raw.iloc[hdr]]
d = raw.iloc[hdr + 1:, [0, cols.index("Beef & Veal Total")]].dropna()
d.columns = ["destination", "tonnes"]
d["country"] = d["destination"].astype(str).str.strip().map(NAMES)
y2025 = d.dropna().groupby("country")["tonnes"].sum().round(0).astype(int)

out = pd.DataFrame({"tonnes_2015": y2015, "tonnes_2025": y2025})
totals = out.loc["TOTAL"]
out = out.drop("TOTAL").reset_index(names="country")
out["change"] = ((out["tonnes_2025"] - out["tonnes_2015"]) / out["tonnes_2015"]).round(3)
long = out.melt(id_vars=["country", "change"], value_vars=["tonnes_2015", "tonnes_2025"],
                var_name="year", value_name="tonnes")
long["year"] = long["year"].str[-4:]
long.to_csv("data/beef_exports_2015_2025.csv", index=False)

print(f"Total exports: 2015 {totals.tonnes_2015:,} t -> 2025 {totals.tonnes_2025:,} t "
      f"({(totals.tonnes_2025 / totals.tonnes_2015 - 1):+.1%})")
print(out.sort_values("tonnes_2025", ascending=False).to_string(index=False))
