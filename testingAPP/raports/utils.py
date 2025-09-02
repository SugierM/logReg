import os
from django.conf import settings
import pandas as pd
import numpy as np


# Is it even needed?
def get_files():
    files = list(set(os.path.splitext(f)[0] for f in os.listdir(settings.TEMP_DIR)))
    return files


def calculate_WOE(df, meta_data):
    woe_summary = {
                "numerical": [],
                "categorical": [],
            }
    
    numerical_columns = meta_data["columns"]["type"]["numerical"]
    categorical_columns = meta_data["columns"]["type"]["categorical"]
    
    target_column = meta_data["target"]
    target_series = df[target_column]

    # ---------------- Numerical ----------------
    for col in numerical_columns:
        series = df[col].dropna()

        min_val = series.min()
        max_val = series.max()

        # Bin starts at 0
        if min_val < 0:
            shift = abs(min_val)
        elif min_val > 0:
            shift = -min_val
        else:
            shift = 0

        shifted = series + shift
        try:
            bins = pd.qcut(shifted, q=7, duplicates='drop')
        except ValueError:
            continue 

        temp_df = pd.DataFrame({
            "bin": bins,
            "target": target_series.loc[series.index]
        })

        grouped = temp_df.groupby("bin")["target"].agg(["count", "sum"]).copy()
        grouped.columns = ['total', 'bad']
        grouped['good'] = grouped['total'] - grouped['bad']

        total_good = grouped['good'].sum()
        total_bad = grouped['bad'].sum()
        if total_good == 0 or total_bad == 0:
            continue

        grouped['%good'] = grouped['good'] / total_good
        grouped['%bad'] = grouped['bad'] / total_bad
        grouped['woe'] = np.log(grouped['%good'] / grouped['%bad']).replace([np.inf, -np.inf], 0)
        grouped['iv'] = (grouped['%good'] - grouped['%bad']) * grouped['woe']

        for idx, row in grouped.iterrows():
            left = round(idx.left - shift, 3)
            right = round(idx.right - shift, 3)
            bin_name = f"{left} - {right}"
            woe_summary["numerical"].append({
                "col_name": col,
                "bin": bin_name,
                "woe": float(round(row['woe'], 4)),
                "IV": float(round(row['iv'], 6)),
                "shift": shift
            })

    # ---------------- Categorical ----------------
    for col in categorical_columns:
        series = df[col].dropna()
        temp_df = pd.DataFrame({
            "cat": series,
            "target": target_series.loc[series.index]
        })

        grouped = temp_df.groupby("cat")["target"].agg(["count", "sum"]).copy()
        grouped.columns = ['total', 'bad']
        grouped['good'] = grouped['total'] - grouped['bad']

        total_good = grouped['good'].sum()
        total_bad = grouped['bad'].sum()
        if total_good == 0 or total_bad == 0:
            continue

        grouped['%good'] = grouped['good'] / total_good
        grouped['%bad'] = grouped['bad'] / total_bad
        grouped['woe'] = np.log(grouped['%good'] / grouped['%bad']).replace([np.inf, -np.inf], 0)
        grouped['iv'] = (grouped['%good'] - grouped['%bad']) * grouped['woe']

        for idx, row in grouped.iterrows():
            woe_summary["categorical"].append({
                "col_name": col,
                "bin": str(idx),
                "woe": float(round(row['woe'], 4)),
                "IV": float(round(row['iv'], 6))
            })

    return woe_summary