# Setup: GitHub Actions → Snowflake (key pair)

The loaders for sources A, D, E and F run on GitHub Actions and connect as the service user
`SVC_DATABANK_INGEST` with a key pair. Do these steps once. **Never commit the private key.**

## 1. Generate the key pair (on your computer)

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

## 2. Create the service user in Snowflake

Open `snowflake/04_service_user_github.sql`, paste the body of `rsa_key.pub` (without the BEGIN/END lines)
in place of `<PASTE_PUBLIC_KEY_BODY_HERE>`, and run it as `ACCOUNTADMIN`.

## 3. Store the secret and variables in GitHub

```bash
gh secret set SNOWFLAKE_PRIVATE_KEY < rsa_key.p8
gh variable set SNOWFLAKE_ACCOUNT --body "xedwtqk-wk19730"
gh variable set SNOWFLAKE_USER --body "SVC_DATABANK_INGEST"
```

Or in the browser: *Settings → Secrets and variables → Actions*. Then delete `rsa_key.p8` from your computer
or keep it in a password manager.

## 4. Run the workflows

```bash
gh workflow run ingest-d-ecb-fx-api.yml
gh workflow run ingest-e-bdf-snowpipe.yml
gh workflow run ingest-f-app-events.yml
gh workflow run stream-a-card-terminals.yml -f minutes=10 -f per_batch=50
gh run list --limit 5
```

## Run locally instead

```bash
pip install -r ingestion/requirements.txt
export SNOWFLAKE_ACCOUNT=xedwtqk-wk19730 SNOWFLAKE_USER=<your user>   # browser login if no key is set
python -m ingestion.d_ecb_api.ingest_ecb_fx
python -m ingestion.a_tpe_stream.producer --minutes 5
```
