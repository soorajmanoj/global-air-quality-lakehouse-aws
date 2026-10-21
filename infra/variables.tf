variable "project_name" {
    type        = string
    default = "global-air-quality"
    description = "Base prefix for resource naming"
}

variable "environment" {
    type        = string
    default     = "dev"
    description = "Environment identifier"
}