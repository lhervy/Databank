"""
Source E - Banque de France credit-incident registry -> RAW.BDF_REGISTRY
Ingestion method: SNOWPIPE (file landed on a stage, load triggered by REST)

Each day the regulator publishes an extract (simulated here: same format,
fictive data). The loader:
  1. writes the day's CSV extract
  2. PUTs it on the internal stage @DATABANK.INGEST.STG_BDF (encrypted)
  3. calls the Snowpipe REST endpoint insertFiles -> Snowflake loads it
     with serverless compute, exactly once (load history = idempotent)
  4. waits for the load report

Day 1 is a full extract (~2 % of clients flagged); later days are deltas
(new incidents, cleared incidents).

Usage: python -m ingestion.e_bdf_snowpipe.load_bdf_registry [--date 2026-11-02] [--full]
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from ingestion.common.snowflake_conn import connect, log, private_key_pem

PIPE = "DATABANK.INGEST.PIPE_BDF_REGISTRY"
STAGE = "@DATABANK.INGEST.STG_BDF"
N_CLIENTS = 10_000
HEADER = ["client_id", "registry", "incident_flag", "incident_type", "incident_date", "extract_date"]
TYPES = ["REPAYMENT_INCIDENT", "OVERINDEBTEDNESS_PLAN"]


def build_extract(day: date, full: bool, flagged_today: set[str]) -> list[list[str]]:
    rnd = random.Random(day.toordinal())          # same date -> same file (reproducible)
    rows = []
    if full:
        for i in sorted(rnd.sample(range(1, N_CLIENTS + 1), 200)):
            rows.append([f"C{i:06d}", "FICP", "TRUE", rnd.choice(TYPES),
                         (day - timedelta(days=rnd.randint(10, 900))).isoformat(), day.isoformat()])
        return rows
    for i in rnd.sample(range(1, N_CLIENTS + 1), 12):                         # new incidents
        rows.append([f"C{i:06d}", "FICP", "TRUE", rnd.choice(TYPES),
                     (day - timedelta(days=rnd.randint(1, 30))).isoformat(), day.isoformat()])
    for cid in rnd.sample(sorted(flagged_today), min(6, len(flagged_today))):  # cleared incidents
        rows.append([cid, "FICP", "FALSE", "", "", day.isoformat()])
    return rows


def write_csv(rows: list[list[str]], day: date, folder: Path) -> Path:
    path = folder / f"bdf_registry_{day.isoformat()}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(HEADER)
        w.writerows(rows)
    return path


def snowpipe_insert(file_name: str) -> None:
    """Notify Snowpipe through its REST API (key-pair JWT auth)."""
    from snowflake.ingest import SimpleIngestManager, StagedFile

    account = os.environ["SNOWFLAKE_ACCOUNT"].upper()
    manager = SimpleIngestManager(
        account=account,
        host=f"{account.lower()}.snowflakecomputing.com",
        user=os.environ["SNOWFLAKE_USER"].upper(),
        pipe=PIPE,
        private_key=private_key_pem(),
    )
    resp = manager.ingest_files([StagedFile(file_name, None)])
    log.info("Snowpipe insertFiles -> %s", resp.get("responseCode"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--date", type=date.fromisoformat, default=date.today())
    p.add_argument("--full", action="store_true", help="publish a full extract instead of a delta")
    args = p.parse_args()

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM DATABANK.RAW.BDF_REGISTRY")
        first_load = cur.fetchone()[0] == 0
        cur.execute("SELECT DISTINCT CLIENT_ID FROM DATABANK.RAW.BDF_REGISTRY WHERE INCIDENT_FLAG")
        flagged = {r[0] for r in cur.fetchall()}

        rows = build_extract(args.date, args.full or first_load, flagged)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_csv(rows, args.date, Path(tmp))
            log.info("extract %s: %d lines", path.name, len(rows))
            cur.execute(f"PUT 'file://{path.as_posix()}' {STAGE} AUTO_COMPRESS = FALSE OVERWRITE = TRUE")
            log.info("PUT -> %s", cur.fetchone()[6])

        if private_key_pem():
            snowpipe_insert(path.name)
        else:  # laptop / SSO: no JWT for the REST API -> ask the pipe to scan the stage
            try:
                cur.execute(f"ALTER PIPE {PIPE} REFRESH")
                log.info("pipe refresh requested (SSO mode)")
            except Exception as exc:  # noqa: BLE001 - fall back to the pipe's own COPY statement
                log.warning("pipe refresh not available (%s) - running the COPY directly", exc)
                cur.execute("""COPY INTO DATABANK.RAW.BDF_REGISTRY
                    (CLIENT_ID, REGISTRY, INCIDENT_FLAG, INCIDENT_TYPE, INCIDENT_DATE, EXTRACT_DATE, SOURCE_FILE)
                    FROM (SELECT $1, $2, $3, $4, $5, $6, METADATA$FILENAME FROM @DATABANK.INGEST.STG_BDF)
                    FILE_FORMAT = (FORMAT_NAME = 'DATABANK.INGEST.FF_BDF_CSV')""")
                log.info("COPY done: %s", cur.fetchall())
                return

        # wait for Snowpipe's load report
        for _ in range(24):
            time.sleep(5)
            cur.execute(f"""
                SELECT STATUS, ROW_COUNT, FIRST_ERROR_MESSAGE
                FROM TABLE(DATABANK.INFORMATION_SCHEMA.COPY_HISTORY(
                    TABLE_NAME => 'DATABANK.RAW.BDF_REGISTRY',
                    START_TIME => DATEADD(hour, -1, CURRENT_TIMESTAMP())))
                WHERE FILE_NAME ILIKE '%{path.name}'
                ORDER BY LAST_LOAD_TIME DESC LIMIT 1""")
            res = cur.fetchone()
            if res:
                log.info("Snowpipe load: status=%s rows=%s error=%s", *res)
                if res[0] != "Loaded":
                    raise SystemExit(1)
                return
        log.warning("no load report yet - check SELECT SYSTEM$PIPE_STATUS('%s')", PIPE)


if __name__ == "__main__":
    main()
