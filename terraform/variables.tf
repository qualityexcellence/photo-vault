variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "postgres_machine_type" {
  description = "Cloud SQL machine type"
  type        = string
  default     = "db-f1-micro"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "photo_user"
  sensitive   = true
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}
