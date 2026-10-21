# School Immunisation Tracking System

A prototype system that replaces spreadsheet-based school immunisation reporting with a standardised submission form, a structured cloud database and an interactive dashboard.

> **AI Capstone Project (group of 6) using entirely synthetic data.** No real health records are included. The client is described generically as "a state health department".

## The Problem

School vaccination coverage was tracked in separate Excel files. That made data collection inconsistent, trends hard to spot and low-coverage schools slow to identify.

## What We've Built

```
Microsoft Forms → Excel (OneDrive) → Power Automate → Azure SQL → Power BI
```

- **Microsoft Forms**: standard submission form for nurses
- **Power Automate**: detects new responses and loads them into a staging table
- **Azure SQL**: staging table, production tables and a stored procedure that validates and promotes data
- **Row-level security**: each district coordinator only sees their own schools
- **Power BI**: dashboards for overall coverage, school-level analysis, multi-year trends and operational follow-up (red/amber/green status against coverage thresholds)

## My contribution

I designed and built the database layer (report Section 4) - the Azure SQL relational schema, computed columns, staging table and stored procedure, the Python data-loading script, the row-level security policies, and the validation checks run against the data.

## What's in this repo

| Path | Description |
|------|-------------|
| `load_dummy_data.py` | Loads the synthetic dataset into the staging and production tables (credentials are read from environment variables) |
| `sql/usp_ProcessStagingData.sql` | Stored procedure that moves staged rows into the production tables |
| `sql/row_level_security.sql` | Row-level security setup (all accounts are placeholders) |

The synthetic dataset and Power BI file are not included.

## Database Design

A star schema: `VaccinationRecords` is the fact table, with `Schools` and `VaccineTypes` as dimensions. It also has a `StagingTable` for raw submissions and an `LHD_UserMapping` table for security. Computed columns calculate consent rate and vaccination rate directly from the stored counts.

## Running the Loader

Set these environment variables, then run the script:

```
DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD
```

## Limitations

- **All data is synthetic.** It was generated with Excel formulas, with consents set at 70–90% of enrolments and vaccinations at 70–90% of consents. The strong correlation between consent rate and coverage (r ≈ 0.91) comes from how the data was generated, so it's not a real-world finding. It demonstrates that the pipeline and dashboard can surface such a relationship.
- This is a prototype. Production use would need real data, stronger validation, upsert logic to prevent duplicate loads, and a finalised Power BI Service setup.
- Herd immunity thresholds are applied in Power BI rather than stored in the database.

## Tech

Azure SQL · T-SQL · Python (pandas, pyodbc) · Power BI · Power Automate · Microsoft Forms
