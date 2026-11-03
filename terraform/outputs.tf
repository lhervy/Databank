output "bi_warehouse" {
  value = module.bi_warehouse.name
}

output "reviewer_role" {
  value = snowflake_account_role.reviewer.name
}

output "evidence_schema" {
  value = snowflake_schema.evidence.fully_qualified_name
}
