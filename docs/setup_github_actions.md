# Setup: GitHub Actions → Snowflake (key pairs)

GitHub needs to log in to Snowflake for two jobs: the **loaders** (sources A, D, E, F, including the
containerised job) and **Terraform**. Each job has its own service user and its own key pair, so a leaked
key only affects one job. Free: no paid service is involved.

A key pair is two files: a **private key** (secret, goes only into GitHub) and a **public key** (not
secret, goes into Snowflake). Do these steps once. **Never commit a private key** (`.gitignore` blocks
`*.p8`).

## 1. Generate the two key pairs (on your computer, in a terminal)

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_ingest.p8 -nocrypt
openssl rsa -in rsa_ingest.p8 -pubout -out rsa_ingest.pub

openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_terraform.p8 -nocrypt
openssl rsa -in rsa_terraform.p8 -pubout -out rsa_terraform.pub
```

## 2. Register the public keys in Snowflake

Open `snowflake/04_service_user_github.sql`, paste the body of `rsa_ingest.pub` and `rsa_terraform.pub`
(the text between the BEGIN and END lines, on one line) in place of the two placeholders, and run it as
`ACCOUNTADMIN`. It creates both service users, gives them their roles, and creates the encrypted stage that
stores the Terraform state.

## 3. Store the private keys in GitHub

```bash
gh secret set SNOWFLAKE_PRIVATE_KEY    < rsa_ingest.p8
gh secret set SNOWFLAKE_TF_PRIVATE_KEY < rsa_terraform.p8
gh variable set SNOWFLAKE_ACCOUNT --body "xedwtqk-wk19730"
gh variable set SNOWFLAKE_USER --body "SVC_DATABANK_INGEST"
```

Or in the browser: repository → *Settings → Secrets and variables → Actions* → *New repository secret*,
then paste the content of each `.p8` file. Then delete the `.p8` files from your computer, or keep them in a
password manager.

## 4. Run the workflows

| Workflow (Actions tab) | What it proves |
|---|---|
| **D · ECB FX rates** | the containerised job runs in the cloud and loads real ECB rates |
| **E · Banque de France registry** | file → stage → Snowpipe |
| **F · Mobile app events** | file → stage → `COPY INTO` |
| **A · Card terminals** (10 minutes) | micro-batch streaming, live balance in the app |
| **Terraform** with `plan`, then `apply` | infrastructure as code with protected state |

Or from a terminal:

```bash
gh workflow run ingest-d-ecb-fx-api.yml
gh workflow run ingest-e-bdf-snowpipe.yml
gh workflow run ingest-f-app-events.yml
gh workflow run stream-a-card-terminals.yml -f minutes=10 -f per_batch=50
gh workflow run terraform.yml -f action=plan
gh run list --limit 5
```

## Run a loader on your own computer instead

```bash
pip install -r ingestion/requirements.txt
export SNOWFLAKE_ACCOUNT=xedwtqk-wk19730 SNOWFLAKE_USER=<your user>   # browser login if no key is set
python -m ingestion.d_ecb_api.ingest_ecb_fx
```

Or inside the container:

```bash
docker build -f ingestion/Dockerfile -t databank-loader:1.0.0 .
docker run --rm -e SNOWFLAKE_ACCOUNT -e SNOWFLAKE_USER -e SNOWFLAKE_PRIVATE_KEY databank-loader:1.0.0
```
