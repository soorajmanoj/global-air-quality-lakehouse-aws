terraform {
    required_version = ">= 1.5.0"
    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "~>5.0"
      }
      random = {
        source = "hashicorp/random"
        version = "~>3.5"
      }
    }
}

provider "aws" {
    region = "us-east-1"
    profile = "openaq-admin"

    default_tags {
        tags = {
            Project     = "Global Air Quality Lakehouse"
            Environment = "dev"
            ManagedBy   = "Terraform"
        }
    }
}