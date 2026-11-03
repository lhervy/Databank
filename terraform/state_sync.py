"""
Terraform remote state stored in an encrypted Snowflake stage (no paid service needed).

  python terraform/state_sync.py pull   # download the latest state into terraform/ (if any)
  python terraform/state_sync.py push   # upload terraform/terraform.tfstate as a new version

Each push keeps a timestamped copy (versioning) and replaces "latest". The GitHub workflow
runs one Terraform job at a time (concurrency group = lock). Only SYSADMIN can read the stage.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.common.snowflake_conn import connect  # noqa: E402

STAGE = "@DATABANK.OPS.TF_STATE"
HERE = Path(__file__).resolve().parent
STATE = HERE / "terraform.tfstate"


def main(action: str) -> None:
    con = connect(role="SYSADMIN", warehouse="DATABANK_WH")
    cur = con.cursor()
    try:
        if action == "pull":
            cur.execute(f"LIST {STAGE}/latest/")
            if not any(row[0].endswith("latest/terraform.tfstate") for row in cur.fetchall()):
                print("No state yet: first run")
                return
            with tempfile.TemporaryDirectory() as tmp:
                cur.execute(f"GET {STAGE}/latest/terraform.tfstate 'file://{tmp}/'")
                got = Path(tmp) / "terraform.tfstate"
                if got.exists():
                    shutil.copy(got, STATE)
                    print("State downloaded from", STAGE)
                else:
                    print("No state yet: first run")
        elif action == "push":
            if not STATE.exists():
                print("Nothing to upload")
                return
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            run = os.getenv("GITHUB_RUN_ID", "local")
            for prefix in (f"versions/{stamp}_{run}", "latest"):
                cur.execute(f"PUT 'file://{STATE}' {STAGE}/{prefix}/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
            print(f"State uploaded to {STAGE}/latest and {STAGE}/versions/{stamp}_{run}")
        else:
            raise SystemExit("usage: state_sync.py pull|push")
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
