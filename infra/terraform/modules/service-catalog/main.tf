variable "catalog" {
  description = "AegisRAG service catalog."
  type = object({
    services = map(object({
      app             = string
      port            = number
      healthReadyPath = string
      healthLivePath  = string
      dependencies    = list(string)
      env             = map(string)
    }))
  })
}

output "services" {
  description = "Normalized service catalog keyed by service name."
  value       = var.catalog.services
}

output "service_names" {
  description = "Sorted AegisRAG service names."
  value       = sort(keys(var.catalog.services))
}
