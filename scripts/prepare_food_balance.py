"""
Builds data/beef_food_balance_2023.csv for the dumbbell chart.
Run from the repo root:  python scripts/prepare_food_balance.py

Input: data/raw/FAOSTAT_data_en_10-2-2026_food_balance.csv
(FAOSTAT Food Balances, item 'Bovine Meat', elements 'Production' and 'Domestic supply quantity',
all countries, 2023, thousand tonnes). 'Domestic supply' = what a country uses at home:
production + imports - exports (+/- stock changes).

Steps:
1. Keep ten Asia-Pacific countries: Malaysia, its neighbours and Australia's main regional markets.
   China and the United States are left out because their values (7-12 million t) would squash
   every other country into a corner of the chart.
2. Put Production and Domestic supply side by side, and work out the gap and the share produced locally.
Note: FAO's 'Bovine Meat' includes buffalo meat as well as cattle meat.
"""
import pandas as pd

fbs = pd.read_csv("data/raw/FAOSTAT_data_en_10-2-2026_food_balance.csv")
keep = {"Australia": "Australia", "New Zealand": "New Zealand", "Malaysia": "Malaysia",
        "Indonesia": "Indonesia", "Philippines": "Philippines", "Viet Nam": "Vietnam",
        "Thailand": "Thailand", "Republic of Korea": "South Korea",
        "China, Taiwan Province of": "Taiwan", "China, Hong Kong SAR": "Hong Kong"}
w = (fbs[fbs["Area"].isin(keep)]
     .pivot_table(index="Area", columns="Element", values="Value")
     .rename(index=keep, columns={"Production": "produced", "Domestic supply quantity": "used"})
     .reset_index(names="country"))
w["gap"] = w["produced"] - w["used"]
w["self_produced"] = (w["produced"] / w["used"]).round(3)
w["year"] = 2023
w.sort_values("gap", ascending=False).to_csv("data/beef_food_balance_2023.csv", index=False)
print(w.sort_values("gap", ascending=False).to_string(index=False))
