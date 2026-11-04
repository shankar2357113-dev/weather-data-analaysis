# Weather Data Analysis System

A beginner-friendly Flask application for analyzing **recorded weather observations**. It does not forecast weather.

## Features

- Upload a CSV file and validate its required columns.
- Report missing and invalid dates/measurements, duplicates, and rejected rows.
- Analyze temperature, humidity, and rainfall by day or month.
- View temperature and rainfall charts.
- Store validated records in MySQL.
- Download a sample CSV and export the monthly summary.
- Keep units explicit: temperature in °C, humidity in %, rainfall in mm.

## Requirements

- Python 3.10 or newer
- MySQL Server 8.x
- A browser
- Git (for version control)

## 1. Create a virtual environment

### Windows PowerShell

```powershell
cd weather-data-analysis
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this in the current terminal (or use `.\.venv\Scripts\python.exe` directly):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Create the MySQL database

Open MySQL Workbench or MySQL Shell and run `sql/schema.sql`.

Or from PowerShell, if the MySQL client is on PATH:

```powershell
mysql -u root -p < sql/schema.sql
```

The SQL creates the `weather_analysis` database and `weather_records` table.

## 3. Configure the environment

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and enter your MySQL username/password. Do not commit `.env`.

Example:

```dotenv
FLASK_SECRET_KEY=replace-this-with-a-random-secret
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=weather_analysis
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
```

If your MySQL account has no password, leave `MYSQL_PASSWORD=` blank. Prefer a dedicated application user over root for real deployments.

## 4. Start the application

```powershell
python run.py
```

Open <http://127.0.0.1:5000>.

The app requires a reachable MySQL server and a valid `.env` configuration. It will show a clear error if the database cannot be reached.

## 5. Upload data

Use the included `data/sample_weather.csv` file, or download it from the app. Expected CSV headers:

```csv
observation_date,location,temperature,humidity,rainfall
```

Units:
- `temperature`: degrees Celsius
- `humidity`: percent from 0 to 100
- `rainfall`: millimetres, non-negative

The validator accepts common alternate headers such as `date`, `city`, `temp`, `humidity_percent`, and `rainfall_mm`. Check the data-quality report after upload. Missing measurements are not silently converted to zero. Invalid rows are excluded from storage; valid measurements can still be summarized metric-by-metric.

## 6. Project structure

```text
weather-data-analysis/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── analysis.py
│   ├── validation.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   └── error.html
│   └── static/
│       └── css/style.css
├── data/sample_weather.csv
├── sql/schema.sql
├── tests/test_validation.py
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## 7. Run tests

```powershell
python -m unittest discover -s tests -v
```

These tests cover CSV validation and do not require MySQL.

## 8. Git and GitHub

First create an empty repository on GitHub. Do not initialize it with a README if you already have this README locally.

```powershell
git init
git add .
git status
git commit -m "Build weather data analysis application"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/weather-data-analysis.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. If `origin` already exists, inspect it with `git remote -v` rather than adding it again.

### Safe Git checks

Before committing, run:

```powershell
git status
git check-ignore .env
```

`.env` must be ignored. Never commit database passwords, secret keys, personal data, or real credentials.

## Data-quality and interpretation notes

- The temperature screening bounds are configurable broad checks, not universal climate limits.
- Duplicate rows are detected using the observation fields; repeated identical observations are excluded from import.
- Monthly rainfall is the sum of valid rainfall values. If rainfall observations are missing, the sum can understate actual rainfall; the report therefore counts missing values.
- Daily/monthly averages describe available observations and are not automatically a complete-day or complete-month average.
- This is a historical analysis tool, not a forecasting model.
