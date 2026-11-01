-- =====================================================================
-- DATABANK · 01 · Source B - Core banking system (OLTP replica) + CDC
--
-- The bank's operational system holds clients, accounts and positions.
-- Here it is simulated by tables in CORE_BANKING. Changes are captured
-- with Snowflake STREAMS (change data capture) and appended by a TASK to
-- RAW.CORE_BANKING_CHANGES - the change log dbt builds history from.
--
-- Ingestion method: CDC (streams + task), incremental, no full reload.
-- All data is random and fictive. Tables are created only if missing.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;
USE SCHEMA CORE_BANKING;

-- Helper numbers table (used to generate data)
CREATE TABLE IF NOT EXISTS CORE_BANKING.NUMBERS AS
SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS n FROM TABLE(GENERATOR(ROWCOUNT => 100000));

-- ---------------------------------------------------------------------
-- Clients
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS CORE_BANKING.CLIENTS AS
SELECT
    'C' || LPAD(n::STRING, 6, '0')                                              AS client_id,
    first_name,
    last_name,
    LOWER(first_name) || '.' || LOWER(last_name) || n::STRING || '@example.com' AS email,
    'FR76' || LPAD(UNIFORM(0, 99999999999, RANDOM())::STRING, 23, '0')          AS iban,
    DATEADD(day, -UNIFORM(6570, 31000, RANDOM()), CURRENT_DATE())               AS birth_date,
    city,
    CASE WHEN r < 0.80 THEN 'RETAIL' WHEN r < 0.97 THEN 'PREMIUM' ELSE 'PRIVATE' END AS segment,
    DATEADD(day, -UNIFORM(30, 7300, RANDOM()), CURRENT_DATE())                  AS client_since,
    SYSDATE()                                                                   AS updated_at
FROM (
    SELECT n,
        GET(ARRAY_CONSTRUCT('Camille','Lucas','Léa','Hugo','Chloé','Louis','Manon','Gabriel','Inès','Jules',
                            'Sarah','Adam','Emma','Nathan','Jade','Raphaël','Lina','Arthur','Zoé','Yanis'),
            UNIFORM(0, 19, RANDOM()))::STRING AS first_name,
        GET(ARRAY_CONSTRUCT('Martin','Bernard','Dubois','Thomas','Robert','Richard','Petit','Durand','Leroy','Moreau',
                            'Simon','Laurent','Lefebvre','Michel','Garcia','David','Bertrand','Roux','Vincent','Fournier'),
            UNIFORM(0, 19, RANDOM()))::STRING AS last_name,
        GET(ARRAY_CONSTRUCT('Paris','Lyon','Marseille','Toulouse','Nice','Nantes','Strasbourg','Montpellier',
                            'Bordeaux','Lille','Rennes','Grenoble'), UNIFORM(0, 11, RANDOM()))::STRING AS city,
        UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS r
    FROM CORE_BANKING.NUMBERS WHERE n <= 10000
);

-- ---------------------------------------------------------------------
-- Accounts: one current account (with a card token) per client,
-- ~35 % also hold an investment account (PEA / securities account)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS CORE_BANKING.ACCOUNTS AS
SELECT
    'A' || LPAD(ROW_NUMBER() OVER (ORDER BY client_id, account_type)::STRING, 7, '0') AS account_id,
    client_id,
    account_type,
    IFF(account_type = 'CURRENT', 'tok_' || SUBSTR(SHA2(client_id || RANDOM()::STRING), 1, 20), NULL) AS card_token,
    ROUND(IFF(account_type = 'CURRENT', UNIFORM(50::FLOAT, 15000::FLOAT, RANDOM()),
                                        UNIFORM(1000::FLOAT, 150000::FLOAT, RANDOM())), 2)   AS ledger_balance_eur,
    SYSDATE() AS balance_as_of,
    'OPEN'    AS status,
    SYSDATE() AS updated_at
FROM (
    SELECT client_id, 'CURRENT' AS account_type FROM CORE_BANKING.CLIENTS
    UNION ALL
    SELECT client_id, 'INVESTMENT' FROM CORE_BANKING.CLIENTS WHERE UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) < 0.35
);

-- ---------------------------------------------------------------------
-- Merchants (reference data received from the card acquirer)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS CORE_BANKING.MERCHANTS AS
SELECT
    'M' || LPAD(n::STRING, 5, '0') AS merchant_id,
    GET(ARRAY_CONSTRUCT('GROCERIES','RESTAURANTS','TRANSPORT','SHOPPING','HEALTH','LEISURE','UTILITIES','TRAVEL'), c)::STRING AS category,
    GET(GET(ARRAY_CONSTRUCT(
            ARRAY_CONSTRUCT('Marché Frais','Épicerie Lumière','SuperPrix'),
            ARRAY_CONSTRUCT('Bistro du Port','Le Petit Zinc','Sushi Nami'),
            ARRAY_CONSTRUCT('MetroPass','TaxiVille','Station Azur'),
            ARRAY_CONSTRUCT('Maison Clé','ModeLab','TechCorner'),
            ARRAY_CONSTRUCT('Pharmacie Centrale','Opticien Clair','Cabinet Santé'),
            ARRAY_CONSTRUCT('Ciné Lumen','Salle Forme+','Librairie Page'),
            ARRAY_CONSTRUCT('ÉnergieVerte','TéléNet','Eau Claire'),
            ARRAY_CONSTRUCT('Hôtel Horizon','AirVoyage','RailExpress')), c), k)::STRING || ' ' || city AS merchant_name,
    city
FROM (
    SELECT n, UNIFORM(0, 7, RANDOM()) AS c, UNIFORM(0, 2, RANDOM()) AS k,
           GET(ARRAY_CONSTRUCT('Paris','Lyon','Marseille','Toulouse','Nice','Nantes','Strasbourg','Montpellier',
                               'Bordeaux','Lille','Rennes','Grenoble'), UNIFORM(0, 11, RANDOM()))::STRING AS city
    FROM CORE_BANKING.NUMBERS WHERE n <= 400
);

-- ---------------------------------------------------------------------
-- Positions: real US-listed tickers, so they join with the real
-- Marketplace stock prices (source C)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS CORE_BANKING.POSITIONS AS
SELECT
    a.account_id,
    a.client_id,
    t.ticker,
    UNIFORM(1, 150, RANDOM())                                AS quantity,
    ROUND(t.ref_price_usd * UNIFORM(0.6::FLOAT, 1.1::FLOAT, RANDOM()), 2) AS avg_buy_price_usd,
    SYSDATE()                                                AS updated_at
FROM CORE_BANKING.ACCOUNTS a
CROSS JOIN (SELECT * FROM (VALUES
    ('AAPL', 200), ('MSFT', 450), ('NVDA', 140), ('AMZN', 200), ('GOOGL', 180),
    ('META', 600), ('JPM', 250), ('V', 320), ('MA', 520), ('TSLA', 300)) AS v (ticker, ref_price_usd)) t
WHERE a.account_type = 'INVESTMENT'
  AND UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) < 0.3;

-- Views read by the card-terminal producer (source A): tokens and merchant ids
-- only - the producer never sees client identities
CREATE OR REPLACE VIEW CORE_BANKING.V_CARD_TOKENS  AS SELECT card_token FROM CORE_BANKING.ACCOUNTS WHERE card_token IS NOT NULL AND status = 'OPEN';
CREATE OR REPLACE VIEW CORE_BANKING.V_MERCHANT_IDS AS SELECT merchant_id FROM CORE_BANKING.MERCHANTS;
GRANT SELECT ON VIEW CORE_BANKING.V_CARD_TOKENS  TO ROLE DATABANK_INGEST;
GRANT SELECT ON VIEW CORE_BANKING.V_MERCHANT_IDS TO ROLE DATABANK_INGEST;

-- ---------------------------------------------------------------------
-- CDC: streams record every insert / update / delete.
-- SHOW_INITIAL_ROWS = TRUE -> the first capture also delivers the snapshot.
-- ---------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS CORE_BANKING.CLIENTS_STREAM   ON TABLE CORE_BANKING.CLIENTS   SHOW_INITIAL_ROWS = TRUE;
CREATE STREAM IF NOT EXISTS CORE_BANKING.ACCOUNTS_STREAM  ON TABLE CORE_BANKING.ACCOUNTS  SHOW_INITIAL_ROWS = TRUE;
CREATE STREAM IF NOT EXISTS CORE_BANKING.POSITIONS_STREAM ON TABLE CORE_BANKING.POSITIONS SHOW_INITIAL_ROWS = TRUE;

CREATE TABLE IF NOT EXISTS RAW.CORE_BANKING_CHANGES (
    source_table  STRING        COMMENT 'CLIENTS / ACCOUNTS / POSITIONS',
    change_type   STRING        COMMENT 'INSERT or DELETE (an UPDATE is a DELETE + INSERT pair)',
    is_update     BOOLEAN,
    record        VARIANT       COMMENT 'The full row after (INSERT) or before (DELETE) the change',
    captured_at   TIMESTAMP_NTZ
) COMMENT = 'Append-only change log of the core banking system (CDC)';

-- Capture procedure: drains the three streams in ONE transaction
CREATE OR REPLACE PROCEDURE CORE_BANKING.CAPTURE_CHANGES()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    n NUMBER DEFAULT 0;
BEGIN
    BEGIN TRANSACTION;
    INSERT INTO DATABANK.RAW.CORE_BANKING_CHANGES
    SELECT 'CLIENTS', METADATA$ACTION, METADATA$ISUPDATE,
           OBJECT_DELETE(OBJECT_CONSTRUCT(*), 'METADATA$ACTION', 'METADATA$ISUPDATE', 'METADATA$ROW_ID'), SYSDATE()
    FROM DATABANK.CORE_BANKING.CLIENTS_STREAM;
    n := n + SQLROWCOUNT;
    INSERT INTO DATABANK.RAW.CORE_BANKING_CHANGES
    SELECT 'ACCOUNTS', METADATA$ACTION, METADATA$ISUPDATE,
           OBJECT_DELETE(OBJECT_CONSTRUCT(*), 'METADATA$ACTION', 'METADATA$ISUPDATE', 'METADATA$ROW_ID'), SYSDATE()
    FROM DATABANK.CORE_BANKING.ACCOUNTS_STREAM;
    n := n + SQLROWCOUNT;
    INSERT INTO DATABANK.RAW.CORE_BANKING_CHANGES
    SELECT 'POSITIONS', METADATA$ACTION, METADATA$ISUPDATE,
           OBJECT_DELETE(OBJECT_CONSTRUCT(*), 'METADATA$ACTION', 'METADATA$ISUPDATE', 'METADATA$ROW_ID'), SYSDATE()
    FROM DATABANK.CORE_BANKING.POSITIONS_STREAM;
    n := n + SQLROWCOUNT;
    COMMIT;
    RETURN 'Captured ' || n || ' changes';
END;
$$;

-- Activity simulator: clients move, change segment, new clients join.
-- Stands in for the real core banking application.
CREATE OR REPLACE PROCEDURE CORE_BANKING.SIMULATE_ACTIVITY()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    next_id NUMBER;
BEGIN
    UPDATE DATABANK.CORE_BANKING.CLIENTS
    SET city = GET(ARRAY_CONSTRUCT('Paris','Lyon','Marseille','Toulouse','Nice','Nantes','Lille','Rennes'), UNIFORM(0, 7, RANDOM()))::STRING,
        updated_at = SYSDATE()
    WHERE UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) < 0.002;

    UPDATE DATABANK.CORE_BANKING.CLIENTS
    SET segment = 'PREMIUM', updated_at = SYSDATE()
    WHERE segment = 'RETAIL' AND UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) < 0.001;

    SELECT MAX(TO_NUMBER(SUBSTR(client_id, 2))) + 1 INTO :next_id FROM DATABANK.CORE_BANKING.CLIENTS;
    INSERT INTO DATABANK.CORE_BANKING.CLIENTS
    SELECT 'C' || LPAD((:next_id + n - 1)::STRING, 6, '0'), 'Nouveau', 'Client', 'new.client' || (:next_id + n - 1)::STRING || '@example.com',
           'FR76' || LPAD(UNIFORM(0, 99999999999, RANDOM())::STRING, 23, '0'),
           DATEADD(day, -UNIFORM(6570, 25000, RANDOM()), CURRENT_DATE()), 'Paris', 'RETAIL', CURRENT_DATE(), SYSDATE()
    FROM DATABANK.CORE_BANKING.NUMBERS WHERE n <= 2;

    RETURN 'Core banking activity simulated';
END;
$$;

-- Tasks (created suspended; started by 07_orchestration.sql)
CREATE OR REPLACE TASK CORE_BANKING.T_SIMULATE_ACTIVITY
    WAREHOUSE = DATABANK_WH
    SCHEDULE  = '10 MINUTE'
    COMMENT   = 'Simulates the core banking application (would not exist in production)'
AS CALL CORE_BANKING.SIMULATE_ACTIVITY();

-- First capture now: delivers the initial snapshot into the change log
CALL CORE_BANKING.CAPTURE_CHANGES();

SELECT source_table, change_type, COUNT(*) AS n
FROM RAW.CORE_BANKING_CHANGES GROUP BY 1, 2 ORDER BY 1, 2;
