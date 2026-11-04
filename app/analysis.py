import io
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def dataframe_from_records(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    for col in ["temperature", "humidity", "rainfall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def build_monthly_summary(df):
    if df.empty:
        return pd.DataFrame(columns=[
            "location", "month", "avg_temperature", "min_temperature",
            "max_temperature", "avg_humidity", "total_rainfall",
            "temperature_count", "humidity_count", "rainfall_count"
        ])
    work = df.copy()
    work["month"] = work["observation_date"].dt.to_period("M").astype(str)
    grouped = work.groupby(["location", "month"], dropna=False)
    summary = grouped.agg(
        avg_temperature=("temperature", "mean"),
        min_temperature=("temperature", "min"),
        max_temperature=("temperature", "max"),
        avg_humidity=("humidity", "mean"),
        total_rainfall=("rainfall", "sum"),
        temperature_count=("temperature", "count"),
        humidity_count=("humidity", "count"),
        rainfall_count=("rainfall", "count"),
    ).reset_index()
    # If every rainfall value in a month is missing, do not report a false zero.
    rainfall_counts = grouped["rainfall"].count().reset_index(name="rainfall_count_check")
    summary = summary.merge(rainfall_counts, on=["location", "month"], how="left")
    summary.loc[summary["rainfall_count_check"] == 0, "total_rainfall"] = np.nan
    summary = summary.drop(columns=["rainfall_count_check"])
    return summary

def build_daily_summary(df):
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    work["date"] = work["observation_date"].dt.date.astype(str)
    return work.groupby(["location", "date"]).agg(
        min_temperature=("temperature", "min"),
        max_temperature=("temperature", "max"),
        avg_temperature=("temperature", "mean"),
        avg_humidity=("humidity", "mean"),
        total_rainfall=("rainfall", "sum"),
        temperature_count=("temperature", "count"),
        humidity_count=("humidity", "count"),
        rainfall_count=("rainfall", "count"),
    ).reset_index()

def plot_to_base64(df, kind="temperature"):
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    work = df.copy()
    if kind == "temperature":
        monthly = work.assign(month=work["observation_date"].dt.to_period("M").astype(str))
        line = monthly.groupby("month")["temperature"].mean().dropna()
        if line.empty:
            plt.close(fig)
            return None
        ax.plot(line.index, line.values, marker="o", linewidth=2)
        ax.set_title("Monthly Average Temperature")
        ax.set_ylabel("Temperature (°C)")
        ax.set_xlabel("Month")
    elif kind == "rainfall":
        monthly = work.assign(month=work["observation_date"].dt.to_period("M").astype(str))
        bars = monthly.groupby("month")["rainfall"].sum(min_count=1).dropna()
        if bars.empty:
            plt.close(fig)
            return None
        ax.bar(bars.index, bars.values)
        ax.set_title("Monthly Total Rainfall")
        ax.set_ylabel("Rainfall (mm)")
        ax.set_xlabel("Month")
    else:
        plt.close(fig)
        return None
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")

def to_display_records(df, limit=100):
    if df.empty:
        return []
    display = df.head(limit).copy()
    for col in display.columns:
        if pd.api.types.is_datetime64_any_dtype(display[col]):
            display[col] = display[col].dt.strftime("%Y-%m-%d")
        elif display[col].dtype == "object":
            display[col] = display[col].map(lambda x: x.isoformat() if hasattr(x, "isoformat") else x)
    display = display.astype(object).where(pd.notna(display), "—")
    return display.to_dict(orient="records")
