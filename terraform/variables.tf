variable "organization_name" {
  description = "First part of the account identifier xedwtqk-wk19730"
  type        = string
  default     = "XEDWTQK"
}

variable "account_name" {
  description = "Second part of the account identifier xedwtqk-wk19730"
  type        = string
  default     = "WK19730"
}

variable "user" {
  description = "Service user Terraform logs in with (key-pair authentication)"
  type        = string
  default     = "SVC_DATABANK_TERRAFORM"
}

variable "database" {
  description = "Database created by snowflake/00_account_setup.sql"
  type        = string
  default     = "DATABANK"
}
