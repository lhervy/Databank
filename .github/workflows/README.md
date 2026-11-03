# `.github/workflows/`: schedules and automatic checks

GitHub Actions runs these files. Each run starts on a brand-new temporary machine, installs the exact
versions listed in `ingestion/requirements.txt`, does its job and is deleted.

| File | What it does | When it runs |
|---|---|---|
| [`ingest-d-ecb-fx-api.yml`](ingest-d-ecb-fx-api.yml) | builds the loader Docker image and loads the new ECB exchange rates **inside the container** (source D) | Monday–Friday 15:30 UTC (16:30 Paris), after the ECB publishes |
| [`ingest-e-bdf-snowpipe.yml`](ingest-e-bdf-snowpipe.yml) | sends the day's Banque de France file through Snowpipe (source E) | Monday–Friday 06:00 UTC (07:00 Paris) |
| [`ingest-f-app-events.yml`](ingest-f-app-events.yml) | loads the latest app event file (source F) | every day at 05:00, 11:00 and 17:00 UTC |
| [`stream-a-card-terminals.yml`](stream-a-card-terminals.yml) | streams card payments for N minutes (source A) | **manually**, before a demo (streaming all day would waste credits) |
| [`terraform.yml`](terraform.yml) | Terraform `plan` or `apply`, with the state pulled from and pushed to an encrypted Snowflake stage | **manually** |
| [`ci.yml`](ci.yml) | checks every change: Python lint, imports, `dbt parse`, Docker image build + smoke test, `terraform fmt` + `validate` | on every push and pull request |

Every workflow can also be started by hand: *Actions* tab → choose the workflow → **Run workflow**.

## How GitHub logs in to Snowflake

With a **key pair**, not a password (a scheduled job cannot type a password or approve MFA):

- the public key is attached to the service user `SVC_DATABANK_INGEST` in Snowflake;
- the private keys are stored as the encrypted GitHub secrets `SNOWFLAKE_PRIVATE_KEY` (loaders) and `SNOWFLAKE_TF_PRIVATE_KEY` (Terraform);
- the account and user names are GitHub variables (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`).

Setup steps: [docs/setup_github_actions.md](../../docs/setup_github_actions.md).
