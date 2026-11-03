# `terraform/`: infrastructure as code

Terraform declares Snowflake resources in files that are reviewed and versioned like the rest of the code.
The core platform was built first with the re-runnable SQL scripts in [`snowflake/`](../snowflake/); this
folder declares the resources added since then, using the Terraform workflow seen in class.

## Status

**Applied on 3 November 2026** from GitHub Actions: `plan` (no error), then `apply`. Checked in Snowflake:
`DATABANK_BI_WH` exists (XSMALL, 60 s auto-suspend), role `DATABANK_REVIEWER` exists (owned by
`SECURITYADMIN`), schema `DATABANK.EVIDENCE` exists, and the state is stored as
`@OPS.TF_STATE/latest/terraform.tfstate` plus a dated copy in `versions/`.

## What is declared here

| Resource | Why the pipeline needs it |
|---|---|
| Warehouse `DATABANK_BI_WH` (through a reusable module) | dashboards and reviewers get their own compute, so reading never slows dbt or the loaders; suspends after 60 s |
| Schema `DATABANK.EVIDENCE` | stores the proof that the pipeline works (incident drills, verification results) |
| Role `DATABANK_REVIEWER` + grants | read-only access for the professor and jury to Gold (`MARTS`), monitoring (`OPS`) and `EVIDENCE` |

## How it runs (free, no paid service)

GitHub → *Actions* → **Terraform · Snowflake resources** → *Run workflow*, with `plan` or `apply`.

| Step | Command | What to say about it |
|---|---|---|
| 1 | `python terraform/state_sync.py pull` | downloads the latest state from the encrypted stage |
| 2 | `terraform init` | downloads the Snowflake provider, pinned to `~> 2.22` (same reflex as the Docker image) |
| 3 | `terraform plan` | shows what would change and changes nothing; reviewed before any apply |
| 4 | `terraform apply` | only when the run is started with `apply` |
| 5 | `python terraform/state_sync.py push` | uploads the new state as a new version |

On every change to the repository, CI also runs `terraform fmt -check` and `terraform validate`.

## The state: protected

The state file maps the code to real objects and can contain sensitive values, so:

- **never in Git**: `.gitignore` excludes `*.tfstate`;
- **remote**: stored in the Snowflake stage `DATABANK.OPS.TF_STATE`, encrypted (`SNOWFLAKE_SSE`);
- **versioned**: every apply keeps a timestamped copy in `versions/`;
- **locked**: the workflow's concurrency group allows one Terraform run at a time;
- **access-controlled**: only the `SYSADMIN` role can read or write the stage.

In a company we would use an S3 bucket (`backend "s3"` with `use_lockfile = true`) or HCP Terraform;
we chose the Snowflake stage because it costs nothing and needs no extra account.

## Authentication

Terraform logs in as its own service user `SVC_DATABANK_TERRAFORM` with a key pair, separate from the
loaders' user. The private key is the GitHub secret `SNOWFLAKE_TF_PRIVATE_KEY`, read from the environment;
it never appears in the code. Roles: `SYSADMIN` (warehouses, schemas) and `SECURITYADMIN` (roles, grants).

## Manual steps that remain (expected)

| Step | Why it cannot be in Terraform here |
|---|---|
| Creating the Snowflake trial account and the first admin user | Terraform needs an account to connect to |
| Creating the two service users and registering their public keys (`snowflake/04_service_user_github.sql`) | Terraform needs a user to log in with |
| Creating the state stage `OPS.TF_STATE` | the state needs somewhere to live before the first run |
| Adding the private keys as GitHub secrets | secrets are entered by a person, never by code |
| Attaching the resource monitor to `DATABANK_BI_WH` (`ALTER WAREHOUSE … SET RESOURCE_MONITOR = DATABANK_RM`) | only `ACCOUNTADMIN` can attach a resource monitor |
| The objects built before Terraform (`snowflake/00`–`09`) | next step: bring them under Terraform with `import` blocks |
