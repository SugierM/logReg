import os
from django.conf import settings
import json

def get_files() -> list:
    # Returns list of files in temp directory (For each dataframe only main name part)
    files = list(set(os.path.splitext(f)[0] for f in os.listdir(settings.TEMP_DIR)))
    return files


def get_unique_filename(dir, file) -> str:
    # Returns unique file name. If file with given name exists add number to avoid duplicate names
    base, ext = os.path.splitext(file)
    print(f"File: {file}")
    print(f"Extension: {ext}")
    counter = 1
    candidate = os.path.join(dir, file)

    while os.path.exists(candidate + ".pkl"): # Maybe not the best idea
        candidate = os.path.join(dir, f"{base}({counter}){ext}")
        counter += 1

    return candidate


def get_column_names(path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["columns"]["all"]


def perform_save(df, df_path:str, additional_info:dict=None) -> None:
    """
    Saves DataFrame and its metadata."
    """
    df.to_pickle(df_path + ".pkl")
    
    meta_data = {
        "columns": {
            "all": df.columns.tolist(),
            "type": {
                "numerical": df.select_dtypes(include=["number"]).columns.tolist(),
                "categorical": df.select_dtypes(include=["category", "bool"]).columns.tolist(),
                "date": df.select_dtypes(include=["datetime64[ns]"]).columns.tolist(),
                "other": df.select_dtypes(exclude=["number", "category", "bool", "datetime64[ns]"]).columns.tolist()
            }
        }
    }

    if additional_info:
        meta_data |= additional_info

    with open(f"{df_path}.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=4, ensure_ascii=False)

