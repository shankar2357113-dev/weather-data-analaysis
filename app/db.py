import mysql.connector
from mysql.connector import Error
from flask import current_app

def get_connection():
    return mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        port=current_app.config["MYSQL_PORT"],
        database=current_app.config["MYSQL_DATABASE"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        connection_timeout=5,
    )

def insert_records(records):
    """Insert validated records with parameterized SQL; returns inserted count."""
    if not records:
        return 0

    # Insert only if the exact observation is not already stored.
    # MySQL's <=> operator compares NULL values safely.
    sql = (
        "INSERT INTO weather_records "
        "(observation_date, location, temperature, humidity, rainfall) "
        "SELECT %s, %s, %s, %s, %s FROM DUAL "
        "WHERE NOT EXISTS ("
        " SELECT 1 FROM weather_records "
        " WHERE observation_date = %s AND location = %s "
        " AND temperature <=> %s AND humidity <=> %s AND rainfall <=> %s"
        ")"
    )
    connection = get_connection()
    try:
        cursor = connection.cursor()
        expanded_records = [
            tuple(record) + tuple(record)
            for record in records
        ]
        cursor.executemany(sql, expanded_records)
        connection.commit()
        return cursor.rowcount
    except Error:
        connection.rollback()
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        connection.close()

def fetch_records(location=None):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        if location:
            cursor.execute(
                "SELECT observation_date, location, temperature, humidity, rainfall "
                "FROM weather_records WHERE location = %s ORDER BY observation_date",
                (location,),
            )
        else:
            cursor.execute(
                "SELECT observation_date, location, temperature, humidity, rainfall "
                "FROM weather_records ORDER BY observation_date"
            )
        rows = cursor.fetchall()
        return rows
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        connection.close()

def fetch_locations():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT location FROM weather_records ORDER BY location")
        return [row[0] for row in cursor.fetchall()]
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        connection.close()
