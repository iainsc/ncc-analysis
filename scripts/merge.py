import os
import pandas as pd

RAW_DIR = "data/raw"
OUT_FILE = "data/processed/master.csv"

def load_and_normalise(path):
    df = pd.read_csv(path)

    # Normalise column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return df

def main():
    files = sorted(os.listdir(RAW_DIR))
    dfs = []

    for f in files:
        if not f.endswith(".csv"):
            continue
        full_path = os.path.join(RAW_DIR, f)
        dfs.append(load_and_normalise(full_path))

    if dfs:
        master = pd.concat(dfs, ignore_index=True)
        master.to_csv(OUT_FILE, index=False)
        print(f"Updated {OUT_FILE} with {len(master)} rows.")
    else:
        print("No CSV files found.")

if __name__ == "__main__":
    main()
