# Terraform: Photo Vault Infrastructure on Google Cloud Platform

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Store state in GCS bucket (uncomment after first apply)
  # backend "gcs" {
  #   bucket = "photo-vault-terraform-state"
  #   prefix = "production"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "storage.googleapis.com",
    "vision.googleapis.com",
    "bigquery.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "servicenetworking.googleapis.com"
  ])

  service = each.value
  disable_on_destroy = false
}

# Cloud Storage Bucket for Images
resource "google_storage_bucket" "images" {
  name     = "${var.gcp_project_id}-images"
  location = var.gcp_region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis["storage.googleapis.com"]]
}

# Cloud Storage Bucket for Frontend
resource "google_storage_bucket" "frontend" {
  name     = "${var.gcp_project_id}-frontend"
  location = var.gcp_region

  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  depends_on = [google_project_service.required_apis["storage.googleapis.com"]]
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "photo-vault-postgres"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier = "db-f1-micro"

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      backup_retention_days          = 7
    }

    ip_configuration {
      require_ssl = true
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.required_apis["sqladmin.googleapis.com"]]
}

# PostgreSQL Database
resource "google_sql_database" "photo_vault" {
  name     = "photo_vault"
  instance = google_sql_database_instance.postgres.name
}

# PostgreSQL User
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_user" "app_user" {
  name     = "photo_vault_user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# BigQuery Dataset
resource "google_bigquery_dataset" "analytics" {
  dataset_id    = "photo_vault_analytics"
  friendly_name = "Photo Vault Analytics"
  description   = "Analytics for photo vault application"
  location      = var.gcp_region

  access {
    role          = "OWNER"
    user_by_email = google_service_account.cloud_run.email
  }
}

# BigQuery Table for Image Analysis
resource "google_bigquery_table" "image_analysis" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "image_analysis"

  schema = jsonencode([
    {
      name        = "image_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Image ID"
    },
    {
      name        = "user_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "User ID"
    },
    {
      name        = "filename"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Image filename"
    },
    {
      name        = "labels"
      type        = "STRING"
      mode        = "REPEATED"
      description = "Vision AI detected labels"
    },
    {
      name        = "faces_count"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Number of faces detected"
    },
    {
      name        = "text_detected"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Text detected in image"
    },
    {
      name        = "colors"
      type        = "STRING"
      mode        = "REPEATED"
      description = "Dominant colors"
    },
    {
      name        = "file_size"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "File size in bytes"
    },
    {
      name        = "analysis_timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "When analysis was done"
    }
  ])
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "photo-vault-app"
  display_name = "Photo Vault Cloud Run Service Account"
}

# IAM Role: Storage Object Creator
resource "google_project_iam_member" "cloud_run_storage" {
  project = var.gcp_project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# IAM Role: Storage Object Viewer
resource "google_project_iam_member" "cloud_run_storage_viewer" {
  project = var.gcp_project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# IAM Role: Vision AI User
resource "google_project_iam_member" "cloud_run_vision" {
  project = var.gcp_project_id
  role    = "roles/ml.admin"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# IAM Role: BigQuery Data Editor
resource "google_project_iam_member" "cloud_run_bigquery" {
  project = var.gcp_project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# IAM Role: Cloud SQL Client
resource "google_project_iam_member" "cloud_run_sql" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run Service (Backend API)
resource "google_cloud_run_service" "backend" {
  name     = "photo-vault-backend"
  location = var.gcp_region

  template {
    spec {
      service_account_name = google_service_account.cloud_run.email

      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/photo-vault/backend:latest"

        ports {
          container_port = 8000
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.app_user.name}:${random_password.db_password.result}@/photo_vault?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
        }

        env {
          name  = "REDIS_URL"
          value = var.redis_url
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }

        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.images.name
        }

        env {
          name  = "ENVIRONMENT"
          value = "production"
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }

      timeout_seconds = 300
    }

    metadata {
      annotations = {
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_sql_database.photo_vault,
    google_sql_user.app_user
  ]
}

# Cloud Run Public Access
resource "google_cloud_run_iam_member" "public" {
  service = google_cloud_run_service.backend.name
  role    = "roles/run.invoker"
  member  = "allUsers"
  location = var.gcp_region
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "docker" {
  location      = var.gcp_region
  repository_id = "photo-vault"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis["artifactregistry.googleapis.com"]]
}

# Outputs
output "cloud_run_url" {
  description = "Cloud Run API URL"
  value       = google_cloud_run_service.backend.status[0].url
}

output "database_host" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "gcs_images_bucket" {
  description = "GCS bucket for images"
  value       = google_storage_bucket.images.name
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.cloud_run.email
}

output "artifact_registry" {
  description = "Artifact Registry URL"
  value       = google_artifact_registry_repository.docker.repository_url
}

output "db_user_password" {
  description = "Database user password (save this securely!)"
  value       = random_password.db_password.result
  sensitive   = true
}
