# Same account, two roles (least privilege):
#   SYSADMIN      creates warehouses and schemas
#   SECURITYADMIN creates roles and grants
# The private key is NOT in the code: the provider reads it from the environment variable
# SNOWFLAKE_PRIVATE_KEY (a GitHub encrypted secret in CI, a local file never committed otherwise).
provider "snowflake" {
  organization_name = var.organization_name
  account_name      = var.account_name
  user              = var.user
  authenticator     = "SNOWFLAKE_JWT"
  role              = "SYSADMIN"
}

provider "snowflake" {
  alias             = "security"
  organization_name = var.organization_name
  account_name      = var.account_name
  user              = var.user
  authenticator     = "SNOWFLAKE_JWT"
  role              = "SECURITYADMIN"
}
