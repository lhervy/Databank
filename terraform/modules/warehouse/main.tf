# Module: one Snowflake warehouse with Databank's cost rules built in.
terraform {
  required_providers {
    snowflake = { source = "snowflakedb/snowflake" }
  }
}

variable "name" { type = string }
variable "size" { type = string }
variable "comment" {
  type    = string
  default = ""
}

resource "snowflake_warehouse" "this" {
  name                = var.name
  warehouse_size      = var.size
  auto_suspend        = 60 # stops after 60 s idle: no credits used when nobody queries
  auto_resume         = true
  initially_suspended = true
  comment             = var.comment
  # The budget cap (resource monitor DATABANK_RM) can only be attached by ACCOUNTADMIN:
  # done once in SQL, listed in terraform/README.md (manual steps).
}

output "name" {
  value = snowflake_warehouse.this.name
}
