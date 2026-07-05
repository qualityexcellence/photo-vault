variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "aivaultphotosgcp"
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
  default     = "redis://localhost:6379"
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
