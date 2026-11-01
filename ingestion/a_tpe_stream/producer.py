"""
Source A - Card terminals (TPE) -> RAW.TPE_AUTHORIZATIONS
Ingestion method: MICRO-BATCH STREAMING

Simulates the card acquirer pushing authorization messages: every
--interval seconds a small batch of JSON messages is inserted into
Snowflake. The dbt dynamic table fct_card_transactions picks them up
within a minute. (Production equivalent: Kafka + Snowflake Kafka
connector / Snowpipe Streaming.)

Realistic defects are injected on purpose, so the pipeline has work to do:
  ~1 %   network retries (same transaction_id twice)  -> deduplicated in dbt
  ~0.2 % broken messages (no amount)                  -> quarantined in dbt
  ~0.3 % unusually large payments                     -> fraud score
  ~5 %   payments abroad, ~3 % declined

Usage:
  python -m ingestion.a_tpe_stream.producer --minutes 10            # live stream
  python -m ingestion.a_tpe_stream.producer --backfill-days 90      # history, then exit
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

from ingestion.common.snowflake_conn import connect, log, run_id

INSERT_SQL = (
    "INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (RECORD_JSON, PRODUCER_ID, BATCH_ID, INGESTED_AT) "
    "VALUES (%s, %s, %s, %s)"
)
COUNTRIES_ABROAD = ["ES", "IT", "DE", "BE", "PT", "GB", "US", "MA"]


def load_directory(cur) -> tuple[list[str], list[str]]:
    """Card tokens and merchant ids the acquirer knows about."""
    cur.execute("SELECT card_token FROM DATABANK.CORE_BANKING.V_CARD_TOKENS")
    tokens = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT merchant_id FROM DATABANK.CORE_BANKING.V_MERCHANT_IDS")
    merchants = [r[0] for r in cur.fetchall()]
    if not tokens or not merchants:
        raise SystemExit("No card tokens / merchants found - run snowflake/01_core_banking.sql first")
    return tokens, merchants


def make_event(tokens: list[str], merchants: list[str], event_ts: datetime) -> dict:
    r = random.random()
    if r < 0.002:
        amount = None                                         # broken message
    elif r < 0.005:
        amount = round(random.uniform(1200, 5000), 2)         # unusual big spend
    else:
        amount = round(math.exp(random.uniform(0.7, 5.3)), 2)  # 2 EUR to 200 EUR
    merchant = random.choice(merchants)
    event = {
        "transaction_id": str(uuid.uuid4()),
        "card_token": random.choice(tokens),
        "merchant_id": merchant,
        "terminal_id": f"TPE-{merchant}-{random.randint(1, 4)}",
        "currency": "EUR",
        "country": "FR" if random.random() < 0.95 else random.choice(COUNTRIES_ABROAD),
        "status": "DECLINED" if random.random() < 0.03 else "AUTHORIZED",
        "event_ts": event_ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
    }
    if amount is not None:
        event["amount"] = amount
    return event


def to_rows(events: list[dict], producer: str, batch_id: str, ingested_at: datetime) -> list[tuple]:
    rows = []
    for e in events:
        rows.append((json.dumps(e), producer, batch_id, ingested_at.strftime("%Y-%m-%d %H:%M:%S.%f")))
        if random.random() < 0.01:                            # network retry: same message again
            retry_ts = ingested_at + timedelta(seconds=2)
            rows.append((json.dumps(e), producer, batch_id, retry_ts.strftime("%Y-%m-%d %H:%M:%S.%f")))
    return rows


def stream(cur, tokens, merchants, minutes: float, interval: float, per_batch: int) -> int:
    producer = f"producer-{run_id()}"
    end = time.time() + minutes * 60
    total = 0
    while time.time() < end:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        n = max(1, int(random.gauss(per_batch, per_batch * 0.2)))
        # events happened during the last interval, received now
        events = [make_event(tokens, merchants, now - timedelta(seconds=random.uniform(0, interval))) for _ in range(n)]
        rows = to_rows(events, producer, str(uuid.uuid4()), now)
        cur.executemany(INSERT_SQL, rows)
        total += len(rows)
        log.info("micro-batch: %d messages sent (total %d)", len(rows), total)
        time.sleep(interval)
    return total


def backfill(cur, tokens, merchants, days: int, events_per_day: int) -> int:
    """Historical load, one day per batch (bulk insert)."""
    producer = f"backfill-{run_id()}"
    total = 0
    today = datetime.now(timezone.utc).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
    for d in range(days, 0, -1):
        day = today - timedelta(days=d)
        events = [make_event(tokens, merchants, day + timedelta(seconds=random.uniform(0, 86400)))
                  for _ in range(events_per_day)]
        rows = to_rows(events, producer, f"backfill-{day:%Y%m%d}", day + timedelta(days=1))
        for i in range(0, len(rows), 5000):
            cur.executemany(INSERT_SQL, rows[i:i + 5000])
        total += len(rows)
        log.info("backfill %s: %d messages", day.date(), len(rows))
    return total


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--minutes", type=float, default=5, help="how long to stream")
    p.add_argument("--interval", type=float, default=10, help="seconds between micro-batches")
    p.add_argument("--per-batch", type=int, default=50, help="average messages per micro-batch")
    p.add_argument("--backfill-days", type=int, default=0, help="load N days of history instead of streaming")
    p.add_argument("--events-per-day", type=int, default=3300)
    args = p.parse_args()

    with connect() as conn, conn.cursor() as cur:
        tokens, merchants = load_directory(cur)
        log.info("%d cards, %d merchants", len(tokens), len(merchants))
        if args.backfill_days:
            total = backfill(cur, tokens, merchants, args.backfill_days, args.events_per_day)
        else:
            total = stream(cur, tokens, merchants, args.minutes, args.interval, args.per_batch)
    log.info("done: %d messages", total)


if __name__ == "__main__":
    main()
