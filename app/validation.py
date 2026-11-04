import pandas as pd

REQUIRED_COLUMNS = [
    "observation_date", "location", "temperature", "humidity", "rainfall"
]
ALIASES = {
    "date": "observation_date",
    "observationdate": "observation_date",
    "city": "location",
    "place": "location",
    "temp": "temperature",
    "temperature_c": "temperature",
    "humidity_percent": "humidity",
    "rainfall_mm": "rainfall",
    "rain": "rainfall",
}

def _normalise_columns(df):
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        compact = key.replace("_", "")
        renamed[col] = ALIASES.get(key, ALIASES.get(compact, key))
    return df.rename(columns=renamed)

def validate_dataframe(raw_df):
    """Return (valid_df, report). Missing measurements are preserved as NaN.

    Rows with an invalid date, blank location, or physically invalid supplied
    measurement are rejected. Missing individual measurements are retained and
    counted, allowing other metrics on that row to remain useful.
    """
    df = _normalise_columns(raw_df.copy())
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError("Missing required CSV columns: " + ", ".join(missing_columns))

    df = df[REQUIRED_COLUMNS].copy()
    input_rows = len(df)

    df["observation_date"] = pd.to_datetime(
        df["observation_date"], errors="coerce"
    ).dt.date
    df["location"] = df["location"].astype("string").str.strip()
    df.loc[df["location"] == "", "location"] = pd.NA

    for col in ["temperature", "humidity", "rainfall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    invalid_date = df["observation_date"].isna()
    invalid_location = df["location"].isna()
    # A non-empty value that fails numeric parsing is invalid, not merely missing.
    invalid_numeric = {}
    for col in ["temperature", "humidity", "rainfall"]:
        original_missing = raw_df[_find_original_column(raw_df, col)].isna() if _find_original_column(raw_df, col) else pd.Series([True] * len(df))
        invalid_numeric[col] = df[col].isna() & ~original_missing.reset_index(drop=True)

    invalid_temperature = df["temperature"].notna() & ~df["temperature"].between(-90, 60)
    invalid_humidity = df["humidity"].notna() & ~df["humidity"].between(0, 100)
    invalid_rainfall = df["rainfall"].notna() & (df["rainfall"] < 0)

    invalid_any = (
        invalid_date | invalid_location
        | invalid_temperature | invalid_humidity | invalid_rainfall
        | invalid_numeric["temperature"] | invalid_numeric["humidity"]
        | invalid_numeric["rainfall"]
    )

    # Count exact duplicate observations across normalized fields.
    duplicate_mask = df.duplicated(subset=REQUIRED_COLUMNS, keep="first")
    reject_mask = invalid_any | duplicate_mask
    valid = df.loc[~reject_mask].copy()

    report = {
        "input_rows": int(input_rows),
        "accepted_rows": int(len(valid)),
        "rejected_rows": int(reject_mask.sum()),
        "invalid_dates": int(invalid_date.sum()),
        "missing_locations": int(invalid_location.sum()),
        "missing_temperatures": int(df["temperature"].isna().sum()),
        "invalid_temperatures": int((invalid_temperature | invalid_numeric["temperature"]).sum()),
        "missing_humidity": int(df["humidity"].isna().sum()),
        "invalid_humidity": int((invalid_humidity | invalid_numeric["humidity"]).sum()),
        "missing_rainfall": int(df["rainfall"].isna().sum()),
        "invalid_rainfall": int((invalid_rainfall | invalid_numeric["rainfall"]).sum()),
        "duplicate_rows": int(duplicate_mask.sum()),
    }
    return valid, report

def _find_original_column(df, target):
    """Find a source column for a normalized numeric field, if present."""
    aliases = {
        "temperature": {"temperature", "temp", "temperature_c"},
        "humidity": {"humidity", "humidity_percent"},
        "rainfall": {"rainfall", "rain", "rainfall_mm"},
    }
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in aliases[target]:
            return col
    return None
