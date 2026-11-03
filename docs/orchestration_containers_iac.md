# Orchestration, containers and Infrastructure as Code

The last two course sessions covered orchestration (Airflow), containers (Docker) and Infrastructure as
Code (Terraform). This page explains what Databank uses, what it deliberately does not use, and why.
The course's own rule guided every choice: **pick the simplest tool for each position.**

## 1. Orchestration

### Automation vs orchestration

- **Automation** = one job runs by itself on a schedule. Example: the GitHub Action that loads ECB rates
  every working day at 16:30.
- **Orchestration** = several jobs that depend on each other, run in the right order, with failure
  handling and monitoring. Example: our Snowflake task graph.

### Our DAG (task graph in Snowflake)

```
T_00_ROOT              every 15 minutes   capture the core banking changes (CDC)
   │  only if it succeeded
   ▼
T_10_DBT_BUILD         dbt build          Bronze → Silver → Gold, with all 43 tests
   │  only if it succeeded
   ▼
T_20_DBT_FRESHNESS     dbt source freshness   warn if a source stopped arriving
```

Defined in [`snowflake/06_dbt_deploy_and_dag.sql`](../snowflake/06_dbt_deploy_and_dag.sql). In Snowsight:
*Transformation → Tasks → T_00_ROOT → Graph*.

It follows the same shape as the course example (ingest → transform → aggregate → report):

| Course example (report) | Databank |
|---|---|
| Task 1 · Ingestion (`COPY INTO`) | loaders A, D, E, F (GitHub Actions, Snowpipe) + `T_00_ROOT` (CDC) |
| Task 2 · Cleaning, de-duplication | dbt staging models (Silver) |
| Task 3 · Business metrics | dbt marts (Gold) |
| Task 4 · Refresh the dashboard | the Streamlit dashboard reads Gold directly, always the latest version |
| Quality gate | dbt tests inside `T_10_DBT_BUILD` + `T_20_DBT_FRESHNESS` |

### The four things an orchestrator must do, and how we do them

| Need (from the course) | How Databank does it |
|---|---|
| **Fault tolerance**: a failure must not push bad data forward | if a step fails, the next task does not run; inside dbt, a failing test stops the models that depend on it, so Gold keeps its last good version |
| **Dependency management**: B starts only after A succeeds | `AFTER` clauses between the tasks |
| **Resource management**: start and stop compute at the right time | each task wakes the warehouse, which suspends 60 seconds later; the schedule is paused between demos |
| **Monitoring**: see what runs and what failed | task history in Snowsight, `OPS.SOURCE_FRESHNESS`, `OPS.FILE_LOADS`, the dashboard's "Pipeline health" tab |

Every job is **idempotent** (running it twice gives the same result): MERGE for the API, file load
history for Snowpipe and `COPY INTO`, `IF NOT EXISTS` in the setup scripts. So a retry is always safe.

### Why not Airflow or Dagster?

The course lists the options: an external orchestrator, or the warehouse's own features (Snowflake tasks,
dbt schedulers). We chose **Snowflake tasks** because:

- all the transformation work already happens inside Snowflake, so there is no other system to coordinate;
- there is no server to host, secure and pay for (Airflow needs a scheduler, workers and a metadata database);
- the team is small.

**When we would switch to Airflow:** many systems outside Snowflake to coordinate (for example an S3 export,
a machine-learning job and a BI refresh in the same chain), complex retry rules, or a large data team.
Managed Airflow on AWS (MWAA) would keep us on one cloud.

## 2. Containers (Docker)

### The problem Docker solves

"The code works on my laptop but crashes on the server": different Python versions, missing libraries,
a different operating system. A Docker **image** packages the code with its runtime and libraries; a
**container** is a running copy of that image, identical everywhere.

### Our containerised job

The loaders are packaged as one Docker image, [`ingestion/Dockerfile`](../ingestion/Dockerfile), and the
daily ECB job (source D) runs **inside that container** in GitHub Actions
([`ingest-d-ecb-fx-api.yml`](../.github/workflows/ingest-d-ecb-fx-api.yml)): build the image, then
`docker run` the loader, which loads into Bronze and stops.

It follows the four Docker reflexes from the course:

| Reflex | In our Dockerfile |
|---|---|
| Pinned base image and dependencies | `python:3.11.14-slim`; every library pinned with `==` in `ingestion/requirements.txt` |
| Dependencies installed before the code is copied | `requirements.txt` first, then `ingestion/`, so the dependency layer is cached |
| No secret inside the image | the private key is passed with `docker run -e SNOWFLAKE_PRIVATE_KEY` at run time; `.dockerignore` excludes keys and `.env` |
| Non-root user | `USER loader` (uid 10001); CI checks it on every change |

On every change to the repository, CI builds the image and runs a smoke test inside it (imports, non-root user).

### Other places where containers appear

| Part | How it is isolated and reproducible |
|---|---|
| Other loaders (A, E, F) | run on brand-new, disposable GitHub Actions machines with the same pinned versions; they can use the same image (`docker run … python -m ingestion.<loader>`) |
| Dashboard | the Streamlit app runs as a **container** inside Snowflake (container runtime on a compute pool) |

### Where we deliberately do not use Docker

The course slide "When not to use Docker" says: keep it simple when the platform already runs the code,
for example *dbt Projects or Tasks in Snowflake, no container*. That is our case for transformation:

- dbt runs as a native **dbt Project** inside Snowflake, with a fixed dbt version managed by Snowflake;
- orchestration uses Snowflake tasks.

Adding containers there would add images to build, store and update, with no benefit.

## 3. Infrastructure as Code (Terraform)

### What we do

Infrastructure as Code means describing the infrastructure in versioned files instead of clicking in a
console. Databank uses two layers:

- **Terraform** ([`terraform/`](../terraform/)) declares the resources added since the first build: the
  dashboards' warehouse `DATABANK_BI_WH` (through a reusable module), the schema `EVIDENCE` and a
  read-only role for reviewers with its grants. Provider pinned, `plan` before `apply`, run from GitHub
  Actions with its own service user and key.
- **Protected state:** never in Git; stored in an encrypted Snowflake stage (`OPS.TF_STATE`), one version
  per run, one run at a time (lock), readable by `SYSADMIN` only. Free, no extra account.
- **Re-runnable SQL scripts** in [`snowflake/`](../snowflake/) built the core platform before Terraform
  (`CREATE … IF NOT EXISTS`, versioned in Git). Bringing them under Terraform with `import` blocks is the
  next step; the remaining manual steps are listed in [`terraform/README.md`](../terraform/README.md).

### SQL scripts vs Terraform

| | SQL scripts | Terraform |
|---|---|---|
| Describes the infrastructure in files | ✅ | ✅ |
| Versioned in Git | ✅ | ✅ |
| Knows what already exists (state file) | ❌ we rely on `IF NOT EXISTS` | ✅ `terraform.tfstate` |
| Shows the changes before applying them | ❌ | ✅ `terraform plan` |
| Removes drift (manual changes made in the console) | ❌ | ✅ |
| Manages AWS and Snowflake with the same tool | ❌ | ✅ (providers `hashicorp/aws` and `snowflakedb/snowflake`) |

### What the core setup would look like in Terraform

The first lines of `00_account_setup.sql`, written in Terraform (HashiCorp Configuration Language):

```hcl
terraform {
  required_providers {
    snowflake = { source = "snowflakedb/snowflake" }
  }
  backend "s3" {                       # the state file is stored on AWS, as in the course
    bucket = "databank-terraform-state"
    key    = "snowflake/terraform.tfstate"
    region = "eu-west-3"
  }
}

resource "snowflake_warehouse" "transform" {
  name           = "DATABANK_WH"
  warehouse_size = "XSMALL"
  auto_suspend   = 60
  auto_resume    = true
}

resource "snowflake_database" "databank" {
  name    = "DATABANK"
  comment = "Databank - fictive bank data platform"
}

resource "snowflake_schema" "raw" {
  database = snowflake_database.databank.name
  name     = "RAW"
  comment  = "Bronze - data exactly as received from external sources"
}
```

The S3 bucket for the optional auto-ingest (source F) would be declared in the same project with the
`hashicorp/aws` provider, so the whole AWS + Snowflake setup would come from one `terraform apply`.

## 4. Where this project sits on the course's "DevOps levels"

| Level (course) | Databank |
|---|---|
| 1 · Git: versioned code | ✅ everything is in this repository |
| 2 · Git: CI/CD | ✅ automatic checks on every change (`ci.yml`) + scheduled loaders in GitHub Actions |
| 3 · Docker | ✅ loader image (pinned, non-root, no secret) run as a container job; containerised dashboard |
| 4 · Terraform | ✅ warehouse, schema, role and grants in Terraform with protected remote state; core platform in re-runnable SQL |
| 5 · Kubernetes | not needed: no long-running services to replicate |
