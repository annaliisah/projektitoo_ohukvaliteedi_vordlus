from pathlib import Path
import json
import requests
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "staging" / "ohuseire"
OUT_DIR = BASE_DIR / "data" / "processed" / "ohuseire"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "stations": "https://www.ohuseire.ee/api/station/et?type=INDICATOR",
    "indicators": "https://www.ohuseire.ee/api/indicator/et?type=INDICATOR",
}

def fetch_json(url: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def to_dataframe(data):
    if isinstance(data, list):
        return pd.json_normalize(data)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                return pd.json_normalize(value)
        return pd.json_normalize(data)
    raise ValueError("Tundmatu JSON struktuur")

def main():
    for name, url in URLS.items():
        print(f"Küsin: {name}")
        data = fetch_json(url)

        raw_path = RAW_DIR / f"{name}.json"
        save_json(data, raw_path)
        print(f"Raw JSON salvestatud: {raw_path}")

        df = to_dataframe(data)

        csv_path = OUT_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"CSV salvestatud: {csv_path}")

        cols_path = OUT_DIR / f"{name}_columns.txt"
        cols_path.write_text("\n".join(df.columns), encoding="utf-8")
        print(f"Veerunimed salvestatud: {cols_path}")

        print(f"{name}: {len(df)} rida, {len(df.columns)} veergu")
        print("-" * 40)

if __name__ == "__main__":
    main()