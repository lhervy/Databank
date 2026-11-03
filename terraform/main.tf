# Databank resources declared as code.
#   terraform plan  = preview the changes (changes nothing)
#   terraform apply = make them
# The rest of the platform is built by the re-runnable SQL scripts in snowflake/ (see README.md here).

# 1. A dedicated warehouse for dashboards and the professor's read-only access,
#    so reading the dashboards never competes with dbt or the loaders (workload isolation).
module "bi_warehouse" {
  source  = "./modules/warehouse"
  name    = "DATABANK_BI_WH"
  size    = "XSMALL"
  comment = "Dashboards and read-only reviewers - managed by Terraform"
}

# 2. A schema that stores the evidence of the pipeline: incident tests, verification results.
resource "snowflake_schema" "evidence" {
  database = var.database
  name     = "EVIDENCE"
  comment  = "Proof that the pipeline works: test runs, incident drills - managed by Terraform"
}

# 3. A read-only role for the professor / jury: can read Gold and monitoring, nothing else.
resource "snowflake_account_role" "reviewer" {
  provider = snowflake.security
  name     = "DATABANK_REVIEWER"
  comment  = "Read-only access to MARTS, OPS and EVIDENCE - managed by Terraform"
}

# Role hierarchy: SYSADMIN inherits the reviewer role (Snowflake best practice)
resource "snowflake_grant_account_role" "reviewer_to_sysadmin" {
  provider         = snowflake.security
  role_name        = snowflake_account_role.reviewer.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_privileges_to_account_role" "reviewer_warehouse" {
  provider          = snowflake.security
  account_role_name = snowflake_account_role.reviewer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = module.bi_warehouse.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "reviewer_database" {
  provider          = snowflake.security
  account_role_name = snowflake_account_role.reviewer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.database
  }
}

resource "snowflake_grant_privileges_to_account_role" "reviewer_schemas" {
  for_each          = toset(["MARTS", "OPS", snowflake_schema.evidence.name])
  provider          = snowflake.security
  account_role_name = snowflake_account_role.reviewer.name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = "\"${var.database}\".\"${each.value}\""
  }
}

# Read every current and future table/view in Gold and in the evidence schema
resource "snowflake_grant_privileges_to_account_role" "reviewer_select_future" {
  for_each          = toset(["TABLES", "VIEWS", "DYNAMIC TABLES"])
  provider          = snowflake.security
  account_role_name = snowflake_account_role.reviewer.name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = each.value
      in_schema          = "\"${var.database}\".\"MARTS\""
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "reviewer_select_existing" {
  for_each          = toset(["TABLES", "VIEWS", "DYNAMIC TABLES"])
  provider          = snowflake.security
  account_role_name = snowflake_account_role.reviewer.name
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = each.value
      in_schema          = "\"${var.database}\".\"MARTS\""
    }
  }
}
