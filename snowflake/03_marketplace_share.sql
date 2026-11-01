-- =====================================================================
-- DATABANK · 03 · Source C - Market data through Snowflake Marketplace
--
-- Real public data (Nasdaq stock prices, FX rates, ECB statistics),
-- curated by Snowflake, delivered by SECURE DATA SHARING:
-- no copy, no pipeline, no storage cost, always up to date.
--
-- One-time step (UI): Marketplace > "Snowflake Curated Data (Free)" > Get
--   database name: SNOWFLAKE_CURATED_DATA_FREE
-- Free tier = data with a 3-month lag (fine for a demo; the paid tier is real time).
--
-- Ingestion method: data sharing (zero-copy). dbt reads it as a source.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;

-- Let the engineering and analyst roles read the shared database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_CURATED_DATA_FREE TO ROLE DATABANK_ENGINEER;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_CURATED_DATA_FREE TO ROLE DATABANK_ANALYST;

-- What we use from it
SELECT ticker, variable, MAX(date) AS last_date, COUNT(*) AS n_points
FROM SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE.STOCK_PRICE_TIMESERIES
WHERE ticker IN ('AAPL','MSFT','NVDA','AMZN','GOOGL','META','JPM','V','MA','TSLA')
  AND variable = 'post-market_close'
GROUP BY 1, 2 ORDER BY 1;

SELECT base_currency_id, quote_currency_id, MAX(date) AS last_date
FROM SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE.FX_RATES_TIMESERIES
WHERE base_currency_id = 'EUR' AND quote_currency_id IN ('USD','GBP','CHF','JPY')
GROUP BY 1, 2;
