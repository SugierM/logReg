from django.shortcuts import render
import pandas as pd
import os
from django.conf import settings
from .utils import get_files
from .forms import StandardReportForm
import json
from scipy.stats import shapiro, kstest, anderson, norm
import numpy as np
import warnings

# I know they are here
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
# TEMP_DIR
# IMAGES_DIR
# ODT_TEMPLATES

def standard_raport(request):
    context = {}
    std_info = []
    additional_info = []
    numerical_info = []
    categorical_info = []
    data_quality = [] # with correlation
    add_info = []
    if request.method == "POST":
        form = StandardReportForm(request.POST)
        if form.is_valid():
            file_name = form.cleaned_data["files"]

            # load df
            df_path = os.path.join(settings.TEMP_DIR, file_name + ".pkl")
            df = pd.read_pickle(df_path)

            # load metadata
            meta_path = os.path.join(settings.TEMP_DIR, file_name + ".json")
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
            meta_data = meta_data["columns"]

############# General informations
            for col in df:
                series = df[col]
                counts = series.count()
                zero_counts = (series[series == 0]).count() if pd.api.types.is_numeric_dtype(series) else "Not applicable"
                missing_values = series.isnull().sum()
                unique = series.nunique()
                series_type = str(series.dtype)

                std_info.append({
                    "name": col,
                    "counts": counts,
                    "zeros": zero_counts,
                    "missing": missing_values,
                    "missing_per": round(missing_values/counts * 100, 2),
                    "unique": unique,
                    "type": series_type,
                })
                
        ##### For all cols
            woe_summary = {
                "numerical": [],
                "categorical": [],
                "other": []
            }

            target_series = df["DEFAULT_FLAG"] # CHANGE

            # ---------------- Numerical ----------------
            for col in meta_data["type"]["numerical"]:
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
                        "name": bin_name,
                        "woe": float(round(row['woe'], 4)),
                        "IV": float(round(row['iv'], 6)),
                        "shift": shift
                    })

            # ---------------- Categorical ----------------
            for col in meta_data["type"]["categorical"]:
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
                        "name": str(idx),
                        "woe": float(round(row['woe'], 4)),
                        "IV": float(round(row['iv'], 6))
                    })

            # ---------------- Other ----------------
            for col in meta_data["type"]["other"]:
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
                    woe_summary["other"].append({
                        "name": str(idx),
                        "woe": float(round(row['woe'], 4)),
                        "IV": float(round(row['iv'], 6))
                    })

            context["all_columns"] = {}
            context["all_columns"]["woe"] = woe_summary

############# Numerical cols
            numerical_cols = meta_data["type"]["numerical"]
            for col in numerical_cols:
                series: pd.Series = df[col]
                # IQR
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                iqr_lower = (q1 - iqr * 1.5)
                iqr_upper = (q3 + iqr * 1.5)
                iqr_outliers = ((series < iqr_lower) | (series > iqr_upper))
                iqr_count = iqr_outliers.sum()
                iqr_per = round(iqr_count / len(series) * 100, 2)

                # Z-Score
                mean = series.mean()
                std = series.std()
                if std == 0:
                    z_count = 0
                    z_percent = 0.0
                    z_scores= 0.0
                else:
                    z_scores = (series - mean) / std
                    z_outliers = z_scores.abs() > 3
                    z_count = z_outliers.sum()
                    z_percent = round(100 * z_count / len(series), 2)

                # Statistics
                stat_shapiro = shapiro(series)
                stat_ks_test = kstest(z_scores, 'norm')
                stat_anderson = anderson(series)

                anderson_results = []
                for pval, crit in zip(stat_anderson.significance_level, stat_anderson.critical_values):
                    anderson_results.append({
                        "pvalue": round(float(pval) / 100, 3),
                        "critical_value": float(crit),
                        "is_normal": bool(stat_anderson.statistic < crit)
                    })

                # Correlation
                corr_thresh = 0.7 # User determined later
                corr_matrix = df[numerical_cols].corr(method='pearson')

                high_corr_pairs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(len(corr_matrix.columns)):
                        col1 = corr_matrix.columns[i]
                        col2 = corr_matrix.columns[j]
                        corr_value = corr_matrix.iloc[i, j]

                        if abs(corr_value) > corr_thresh:
                            high_corr_pairs.append({
                                "col1": col1,
                                "col2": col2,
                                "corr_val": round(corr_value, 4),
                                "strength": (
                                    "very high" if abs(corr_value) >=0.9 else
                                    "high" if abs(corr_value) >= 0.7 else
                                    "moderate" if abs(corr_value) >= 0.5 else
                                    "low"
                                ),
                                "to_review": abs(corr_value) >= 0.9
                            })

                numerical_info.append({
                    "name": col,
                    "min": round(float(series.min()), 4), 
                    "max": round(float(series.max()), 4),
                    "median": round(float(series.median()), 4),
                    "mean": round(float(mean), 4),
                    "std": round(float(std), 4),
                    "01q": round(float(series.quantile(0.01)), 4),
                    "25q": round(float(q1), 4),
                    "75q": round(float(q3), 4),
                    "99q": round(float(series.quantile(0.99)), 4),
                    "iqr_lower": round(float(iqr_lower), 4),
                    "iqr_upper": round(float(iqr_upper), 4),
                    "iqr_count": round(iqr_count, 4),
                    "iqr_per": round(float(iqr_per), 2),
                    "z_count": z_count,
                    "z_per": round(float(z_percent), 2),

                    "statistics":{
                        "stat_shapiro": {
                            "statistic": float(stat_shapiro.statistic),
                            "pvalue": float(stat_shapiro.pvalue),
                            "is_normal": bool(float(stat_shapiro.pvalue) > 0.05),
                        },
                        "stat_ks_test": {
                            "statistic": float(stat_ks_test.statistic),
                            "pvalue": float(stat_ks_test.pvalue),
                            "is_normal": bool(float(stat_ks_test.pvalue) > 0.05),
                        },
                        "stat_anderson": {
                            "statistic": float(stat_anderson.statistic),
                            "results": anderson_results
                        }
                    }
                })

############# Categorical cols


############# Other type cols


            # Save info :)
            context["cat_info"] = categorical_info
            context["std_info"] = std_info
            context["numerical_info"] = numerical_info
            context["chosen"] = file_name

    else:
        form = StandardReportForm()

    context["form"] = form
    return render(request, "std_report.html", context)