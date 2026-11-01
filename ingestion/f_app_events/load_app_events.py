"""
Source F - Mobile app events -> RAW.APP_EVENTS
Ingestion method: BATCH COPY INTO from a stage (files)

The mobile app backend exports events as newline-delimited JSON files
(simulated here). The loader:
  1. generates the events of the last --hours hours into a .json.gz file
  2. PUTs it on @DATABANK.INGEST.STG_APP_EVENTS/<yyyy>/<mm>/<dd>/
  3. runs COPY INTO: Snowflake remembers loaded files for 64 days, so a
     re-run loads 0 files (idempotent)

Production: the backend writes to S3 and a Snowpipe with AUTO_INGEST
loads each file on arrival (see snowflake/02_raw_landing.sql, optional block).
--target s3 uploads to that bucket instead (needs AWS credentials).

Usage: python -m ingestion.f_app_events.load_app_events [--hours 6] [--target stage|s3]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion.common.snowflake_conn import connect, log

STAGE = "@DATABANK.INGEST.STG_APP_EVENTS"
EVENT_TYPES = [("login", None, 0.25), ("screen_view", "home", 0.20), ("screen_view", "transactions", 0.18),
               ("screen_view", "budget", 0.08), ("screen_view", "investments", 0.07), ("budget_set", "budget", 0.04),
               ("notification_open", "transactions", 0.10), ("card_freeze", "cards", 0.01),
               ("transfer_start", "transfers", 0.05), ("logout", None, 0.02)]
DEVICES = [("ios", 0.55), ("android", 0.40), ("web", 0.05)]


def weighted(choices):
    return random.choices([c[:-1] if len(c) > 2 else c[0] for c in choices], weights=[c[-1] for c in choices])[0]


def generate(hours: int, n_events: int) -> list[dict]:
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    events = []
    for _ in range(n_events):
        etype, screen = weighted(EVENT_TYPES)
        events.append({
            "event_id": str(uuid.uuid4()),
            "client_id": f"C{random.randint(1, 10_000):06d}",
            "event_type": etype,
            "screen": screen,
            "device": weighted(DEVICES),
            "app_version": random.choice(["5.2.0", "5.2.1", "5.3.0"]),
            "event_ts": (end - timedelta(seconds=random.uniform(0, hours * 3600))).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        })
    return events


def write_file(events: list[dict], folder: Path) -> Path:
    path = folder / f"app_events_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{uuid.uuid4().hex[:6]}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=int, default=6)
    p.add_argument("--events-per-hour", type=int, default=2000)
    p.add_argument("--target", choices=["stage", "s3"], default="stage")
    args = p.parse_args()

    events = generate(args.hours, args.hours * args.events_per_hour)
    with tempfile.TemporaryDirectory() as tmp:
        path = write_file(events, Path(tmp))
        prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        log.info("file %s: %d events", path.name, len(events))

        if args.target == "s3":   # production path: S3 + Snowpipe auto-ingest does the load
            import boto3
            bucket = os.environ["DATABANK_S3_BUCKET"]
            boto3.client("s3").upload_file(str(path), bucket, f"app-events/{prefix}/{path.name}")
            log.info("uploaded to s3://%s/app-events/%s/ - Snowpipe auto-ingest will load it", bucket, prefix)
            return

        with connect() as conn, conn.cursor() as cur:
            cur.execute(f"PUT 'file://{path.as_posix()}' {STAGE}/{prefix}/ AUTO_COMPRESS = FALSE")
            log.info("PUT -> %s", cur.fetchone()[6])
            cur.execute(f"""
                COPY INTO DATABANK.RAW.APP_EVENTS (RECORD, SOURCE_FILE, FILE_ROW)
                FROM (SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER FROM {STAGE}/{prefix}/)
                FILE_FORMAT = (FORMAT_NAME = 'DATABANK.INGEST.FF_NDJSON')
                ON_ERROR = 'SKIP_FILE'""")
            for row in cur.fetchall():   # one row per file, or one status row if nothing new
                log.info("COPY result: %s", row[:4])


if __name__ == "__main__":
    main()
