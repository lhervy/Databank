terraform {
  required_version = ">= 1.9.0"

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.22" # pinned major version: same reflex as the Docker image
    }
  }

  # State: kept OUT of Git. The workflow .github/workflows/terraform.yml downloads it from an
  # encrypted Snowflake stage (DATABANK.OPS.TF_STATE) before each run and uploads it after:
  # remote, versioned (one file per run), locked (one run at a time) and access-controlled.
  backend "local" {
    path = "terraform.tfstate"
  }
}
