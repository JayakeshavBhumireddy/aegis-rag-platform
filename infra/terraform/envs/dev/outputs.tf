output "environment" {
  description = "Environment name."
  value       = local.environment
}

output "project" {
  description = "Project name."
  value       = local.project
}

output "service_names" {
  description = "Services included in the local deployment catalog."
  value       = module.service_catalog.service_names
}
