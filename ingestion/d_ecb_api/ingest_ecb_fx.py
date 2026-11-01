"""
Source D - European Central Bank Data Portal API -> RAW.ECB_FX_RATES
Ingestion method: REST API PULL, INCREMENTAL (watermark) + idempotent MERGE

Every working day the ECB publishes euro reference rates (~16:00 CET).
This loader:
  1. reads the watermark = last rate_date already loaded in Snowflake
  2. calls the public API for the days after the watermark only
  3. MERGEs the rows on (rate_date, currency): re-running is harmless

API docs: https://data.ecb.europa.eu/help/api/data
Usage:   python -m ingestion.d_ecb_api.ingest_ecb_fx [--start 2024-01-01]
"""
from __future__ import annotations

import argparse
import csv
import io
from datetime import date, datetime, timedelta, timezone

import requests

from ingestion.common.snowflake_conn import connect, log, run_id

API = "https://data-api.ecb.europa.eu/service/data/EXR/D.{currencies}.EUR.SP00.A"
CURRENCIES = ["USD", "GBP", "CHF", "JPY"]
DEFAULT_HISTORY_DAYS = 730


def fetch_rates(start: date, currencies: list[str] = CURRENCIES) -> list[dict]:
    """Daily reference rates from `start` (inclusive). Empty list when nothing new."""
    url = API.format(currencies="+".join(currencies))
    resp = requests.get(url, params={"startPeriod": start.isoformat(), "format": "csvdata"},
                        headers={"Accept": "text/csv"}, timeout=60)
    if resp.status_code == 404:          # ECB answers 404 "No results found" when there is no new data
        return []
    resp.raise_for_status()
    return parse_csv(resp.text)


def parse_csv(text: str) -> list[dict]:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        if not r.get("OBS_VALUE"):
            continue
        rows.append({
            "rate_date": r["TIME_PERIOD"],
            "currency": r["CURRENCY"],
            "base_currency": r["CURRENCY_DENOM"],
            "rate": float(r["OBS_VALUE"]),
            "series_key": r["KEY"],
        })
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=date.fromisoformat, help="force a start date (otherwise: watermark + 1 day)")
    args = p.parse_args()

    with connect() as conn, conn.cursor() as cur:
        if args.start:
            start = args.start
        else:
            cur.execute("SELECT MAX(RATE_DATE) FROM DATABANK.RAW.ECB_FX_RATES")
            watermark = cur.fetchone()[0]
            start = (watermark + timedelta(days=1)) if watermark else date.today() - timedelta(days=DEFAULT_HISTORY_DAYS)
        log.info("watermark -> fetching ECB rates from %s", start)

        rows = fetch_rates(start)
        if not rows:
            log.info("no new rates published since %s - nothing to load", start)
            return
        log.info("received %d rates (%s to %s)", len(rows), rows[0]["rate_date"], rows[-1]["rate_date"])

        loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rid = run_id()
        cur.execute("CREATE TEMPORARY TABLE DATABANK.RAW.TMP_ECB_FX LIKE DATABANK.RAW.ECB_FX_RATES")
        cur.executemany(
            "INSERT INTO DATABANK.RAW.TMP_ECB_FX (RATE_DATE, CURRENCY, BASE_CURRENCY, RATE, SERIES_KEY, LOADED_AT, RUN_ID) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(r["rate_date"], r["currency"], r["base_currency"], r["rate"], r["series_key"], loaded_at, rid) for r in rows],
        )
        cur.execute("""
            MERGE INTO DATABANK.RAW.ECB_FX_RATES t
            USING DATABANK.RAW.TMP_ECB_FX s
               ON t.RATE_DATE = s.RATE_DATE AND t.CURRENCY = s.CURRENCY
            WHEN MATCHED AND t.RATE <> s.RATE THEN UPDATE SET
                 RATE = s.RATE, LOADED_AT = s.LOADED_AT, RUN_ID = s.RUN_ID
            WHEN NOT MATCHED THEN INSERT (RATE_DATE, CURRENCY, BASE_CURRENCY, RATE, SERIES_KEY, LOADED_AT, RUN_ID)
                 VALUES (s.RATE_DATE, s.CURRENCY, s.BASE_CURRENCY, s.RATE, s.SERIES_KEY, s.LOADED_AT, s.RUN_ID)
        """)
        inserted, updated = cur.fetchone()[:2]
        log.info("MERGE done: %s inserted, %s updated", inserted, updated)


if __name__ == "__main__":
    main()
