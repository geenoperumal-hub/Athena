-- bigquery_schemas.sql
CREATE SCHEMA IF NOT EXISTS athena_data;

CREATE TABLE athena_data.startup_profiles (
    startup_id STRING,
    company_name STRING,
    founders ARRAY<STRUCT<
        name STRING,
        background STRING,
        linkedin_url STRING,
        experience_years INT64
    >>,
    problem_statement STRING,
    solution_description STRING,
    market_data STRUCT<
        tam FLOAT64,
        sam FLOAT64,
        som FLOAT64,
        target_market STRING
    >,
    traction_metrics STRUCT<
        mrr FLOAT64,
        arr FLOAT64,
        cac FLOAT64,
        ltv FLOAT64,
        churn_rate FLOAT64,
        user_count INT64
    >,
    financials STRUCT<
        revenue FLOAT64,
        burn_rate FLOAT64,
        funding_requested FLOAT64,
        valuation FLOAT64,
        runway_months INT64
    >,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE athena_data.benchmark_data (
    sector STRING,
    stage STRING,
    metric_name STRING,
    p25 FLOAT64,
    p50 FLOAT64,
    p75 FLOAT64,
    p90 FLOAT64,
    updated_at TIMESTAMP
);

CREATE TABLE athena_data.risk_assessments (
    startup_id STRING,
    risk_category STRING,
    risk_score FLOAT64,
    risk_description STRING,
    evidence ARRAY<STRING>,
    created_at TIMESTAMP
);
