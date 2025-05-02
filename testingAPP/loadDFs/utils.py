import os
from django.conf import settings

def get_files():
    # Returns list of files in temp directory (For each dataframe only main name part)
    files = list(set(os.path.splitext(f)[0] for f in os.listdir(settings.TEMP_DIR)))
    return files


def get_unique_filename(dir, file):
    # Returns unique file name. If file with given name exists add number to avoid duplicate names
    base, ext = os.path.splitext(file)
    counter = 1
    candidate = os.path.join(dir, file)

    while os.path.exists(candidate):
        candidate = os.path.join(dir, f"{base}_{counter}{ext}")
        counter += 1

    return candidate


def get_column_names(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        columns = [line.strip() for line in file]

    return columns


def perform_save(df, df_path, columns):
    # df_path should be without extensions
    # For Example "New_DataFrame"
    df.to_pickle(df_path + ".pkl")

    with open(f"{df_path}.txt", "w", encoding='utf-8') as f:
        for col in columns:
            f.write(col + "\n")