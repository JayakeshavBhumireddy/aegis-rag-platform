terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  project         = "aegis-rag"
  environment     = "dev"
  service_catalog = jsondecode(file("${path.module}/../../../service-catalog/aegis-services.json"))
}

module "service_catalog" {
  source  = "../../modules/service-catalog"
  catalog = local.service_catalog
}
