"""
Shared Snowflake connection for every loader.

Two ways to authenticate, chosen automatically:
  * GitHub Actions / servers: key pair. SNOWFLAKE_PRIVATE_KEY holds the PEM
    private key (from GitHub Secrets). No password, no MFA prompt.
  * Laptop: SSO in the browser (authenticator=externalbrowser) with your own
    Snowflake user - nothing secret stored on disk.

Environment variables:
  SNOWFLAKE_ACCOUNT    e.g. xedwtqk-wk19730
  SNOWFLAKE_USER       SVC_DATABANK_INGEST (Actions) or your user (laptop)
  SNOWFLAKE_PRIVATE_KEY  optional PEM text
  SNOWFLAKE_ROLE       default DATABANK_INGEST
  SNOWFLAKE_WAREHOUSE  default DATABANK_INGEST_WH
"""
from __future__ import annotations

import logging
import os

import snowflake.connector
from cryptography.hazmat.primitives import serialization

log = logging.getLogger("databank")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATABASE = "DATABANK"


def private_key_pem() -> str | None:
    """PEM text of the private key, or None (GitHub may store literal \\n)."""
    pem = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    if not pem:
        return None
    return pem.replace("\\n", "\n").strip() + "\n"


def connect(role: str | None = None, warehouse: str | None = None) -> snowflake.connector.SnowflakeConnection:
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": role or os.getenv("SNOWFLAKE_ROLE", "DATABANK_INGEST"),
        "warehouse": warehouse or os.getenv("SNOWFLAKE_WAREHOUSE", "DATABANK_INGEST_WH"),
        "database": DATABASE,
        "session_parameters": {"QUERY_TAG": "databank-ingestion"},
    }
    pem = private_key_pem()
    if pem:
        key = serialization.load_pem_private_key(pem.encode(), password=None)
        params["private_key"] = key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        auth = "key pair"
    else:
        params["authenticator"] = os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
        auth = params["authenticator"]
    log.info("Connecting to %s as %s (%s)", params["account"], params["user"], auth)
    return snowflake.connector.connect(**params)


def run_id() -> str:
    """Identifier of this run, for lineage columns."""
    if os.getenv("GITHUB_RUN_ID"):
        return f"gha-{os.environ['GITHUB_RUN_ID']}-{os.getenv('GITHUB_RUN_ATTEMPT', '1')}"
    return "local"
