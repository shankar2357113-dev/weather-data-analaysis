import io
import pandas as pd
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from mysql.connector import Error as MySQLError
from .analysis import (
    dataframe_from_records, build_monthly_summary, build_daily_summary,
    plot_to_base64, to_display_records
)
from .db import insert_records, fetch_records, fetch_locations
from .validation import validate_dataframe

bp = Blueprint("main", __name__)

@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a CSV file first.", "error")
        return redirect(url_for("main.index"))
    if not file.filename.lower().endswith(".csv"):
        flash("Only .csv files are accepted.", "error")
        return redirect(url_for("main.index"))

    try:
        raw = pd.read_csv(file, dtype_backend="numpy_nullable")
        valid, report = validate_dataframe(raw)
        if valid.empty:
            flash("No valid rows to import. Review the data-quality report.", "error")
            return render_template("dashboard.html", report=report, monthly=[], daily=[],
                                   temperature_chart=None, rainfall_chart=None,
                                   locations=[], selected_location="All",
                                   records=[], message="No rows were imported.")
        records = []
        for row in valid.itertuples(index=False, name=None):
            date_value, location, temperature, humidity, rainfall = row
            records.append((
                date_value,
                str(location),
                None if pd.isna(temperature) else float(temperature),
                None if pd.isna(humidity) else float(humidity),
                None if pd.isna(rainfall) else float(rainfall),
            ))
        inserted = insert_records(records)
        flash(f"Imported {inserted} validated row(s) into MySQL.", "success")
        return _dashboard_for_location(None, report=report, message=f"Imported {inserted} row(s).")
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        flash(f"CSV validation failed: {exc}", "error")
        return redirect(url_for("main.index"))
    except MySQLError as exc:
        current_app.logger.exception("MySQL operation failed")
        flash("Could not save data to MySQL. Check that MySQL is running and .env credentials/schema are correct.", "error")
        return redirect(url_for("main.index"))
    except Exception:
        current_app.logger.exception("Unexpected upload error")
        flash("The upload failed unexpectedly. Check the terminal logs for details.", "error")
        return redirect(url_for("main.index"))

@bp.route("/dashboard", methods=["GET"])
def dashboard():
    selected = request.args.get("location") or None
    return _dashboard_for_location(selected)

def _dashboard_for_location(location, report=None, message=None):
    try:
        locations = fetch_locations()
        if location and location not in locations:
            location = None
        records = fetch_records(location)
    except MySQLError:
        current_app.logger.exception("Could not load dashboard data")
        flash("Cannot connect to MySQL. Start MySQL and verify your .env settings.", "error")
        return redirect(url_for("main.index"))

    df = dataframe_from_records(records)
    monthly_df = build_monthly_summary(df)
    daily_df = build_daily_summary(df)
    if report is None:
        report = {
            "input_rows": "—", "accepted_rows": "—", "rejected_rows": "—",
            "invalid_dates": "—", "missing_locations": "—",
            "missing_temperatures": "—", "invalid_temperatures": "—",
            "missing_humidity": "—", "invalid_humidity": "—",
            "missing_rainfall": "—", "invalid_rainfall": "—",
            "duplicate_rows": "—",
        }
    return render_template(
        "dashboard.html",
        report=report,
        monthly=to_display_records(monthly_df.round(2)),
        daily=to_display_records(daily_df.round(2)),
        temperature_chart=plot_to_base64(df, "temperature"),
        rainfall_chart=plot_to_base64(df, "rainfall"),
        locations=locations,
        selected_location=location or "All",
        records=to_display_records(df, 100),
        message=message,
    )

@bp.route("/sample.csv", methods=["GET"])
def sample_csv():
    path = current_app.root_path + "/../data/sample_weather.csv"
    return send_file(path, as_attachment=True, download_name="sample_weather.csv", mimetype="text/csv")

@bp.route("/export/monthly.csv", methods=["GET"])
def export_monthly():
    location = request.args.get("location") or None
    try:
        records = fetch_records(location)
    except MySQLError:
        flash("Cannot connect to MySQL to export the summary.", "error")
        return redirect(url_for("main.index"))
    df = dataframe_from_records(records)
    summary = build_monthly_summary(df)
    buffer = io.BytesIO(summary.to_csv(index=False).encode("utf-8"))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="monthly_weather_summary.csv", mimetype="text/csv")
