from django.shortcuts import render
import pandas as pd
import os
from django.conf import settings
from .utils import get_files, calculate_WOE
from .forms import StandardReportForm
import json
from scipy.stats import shapiro, kstest, anderson, norm
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import shutil
import warnings

# I know they are there
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
                
        ##### For mixed cols
            woe_summary = calculate_WOE(df, meta_data)

            context["all_columns"] = {}
            context["all_columns"]["woe"] = woe_summary

############# Numerical cols
            numerical_cols = meta_data["columns"]["type"]["numerical"]
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

            # Correlation
            corr_thresh = 0.7 # User determined later
            corr_matrix = df[numerical_cols].corr(method='pearson')

            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(len(corr_matrix.columns)):
                    if i == j:
                        continue
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
                                "moderate" if abs(corr_value) >= 0.5 else # Both modereate and low stays as in the future it may be usefull for the user
                                "low"
                            ),
                            "to_review": bool(abs(corr_value) >= 0.9)
                        })
            numerical_info.append(high_corr_pairs)
        ##### Images 
            images_dir = settings.IMAGES_DIR
            os.makedirs(images_dir, exist_ok=True)
            numerical_images_path = os.path.join(images_dir, "numerical")
            histogram_path = os.path.join(numerical_images_path, "histogram")
            os.makedirs(histogram_path, exist_ok=True)

            # Histogram
            n_cols = 3
            figsize = (5 * n_cols, 4) # 5X4

            for i in range(0, len(numerical_cols), n_cols):
                cols_batch = numerical_cols[i:i + n_cols]
                n = len(cols_batch)
                fig, axes = plt.subplots(1, n_cols, figsize=figsize)

                for j in range(n_cols):
                    if j < n:
                        col = cols_batch[j]
                        ax = axes[j]
                        df[col].plot.hist(ax=ax, bins=30, edgecolor='black')
                        ax.set_title(col)
                    else:
                        axes[j].axis('off')

                plt.tight_layout()
                filename = os.path.join(histogram_path, f"{i//n_cols + 1}.png")
                plt.savefig(filename)
                plt.close()

                # if os.path.exists(folder_path): # Delete after using not now
                #     shutil.rmtree(folder_path)
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