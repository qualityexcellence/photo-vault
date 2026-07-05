terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  cloud {
    organization = "your-org"
    
    workspaces {
      name = "photo-vault"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudkms.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "vision.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "servicenetworking.googleapis.com",
    "container.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "photo-vault-postgres"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier              = var.postgres_machine_type
    availability_type = "REGIONAL"
    
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 30
      }
    }

    database_flags {
      name  = "cloudsql_iam_authentication"
      value = "on"
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_sql_database" "photo_vault_db" {
  name     = "photo_vault"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Cloud Storage Bucket
resource "google_storage_bucket" "images" {
  name          = "${var.gcp_project_id}-photo-vault-images"
  location      = var.gcp_region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}

# BigQuery Dataset
resource "google_bigquery_dataset" "photo_vault" {
  dataset_id    = "photo_vault"
  friendly_name = "Photo Vault Analytics"
  description   = "Analytics data for photo vault application"
  location      = var.gcp_region

  access {
    role          = "OWNER"
    user_by_email = google_service_account.cloud_run.email
  }
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "photo-vault-app"
  display_name = "Photo Vault Application"
}

# IAM Roles for Service Account
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/cloudsql.client",
    "roles/cloudkms.cryptoKeyDecrypter",
  ])

  project = var.gcp_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run Service
resource "google_cloud_run_service" "api" {
  name     = "photo-vault-api"
  location = var.gcp_region

  template {
    spec {
      service_account_name = google_service_account.cloud_run.email

      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/photo-vault/api:latest"

        env {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_user}:${random_password.db_password.result}@${google_sql_database_instance.postgres.private_ip_address}:5432/photo_vault"
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.images.name
        }

        env {
          name  = "BIGQUERY_DATASET"
          value = google_bigquery_dataset.photo_vault.dataset_id
        }

        env {
          name  = "JWT_SECRET_KEY"
          value = random_password.jwt_secret.result
        }

        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      timeout_seconds = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = "1"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Run Service Public Access
resource "google_cloud_run_service_iam_member" "public_access" {
  service = google_cloud_run_service.api.name
  role    = "roles/run.invoker"
  member  = "allUsers"
  location = var.gcp_region
}

# Cloud Storage Backend for Frontend
resource "google_storage_bucket" "frontend" {
  name          = "${var.gcp_project_id}-photo-vault-frontend"
  location      = var.gcp_region
  force_destroy = false

  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

# Enable public access to frontend bucket
resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# JWT Secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Outputs
output "cloud_run_url" {
  value       = google_cloud_run_service.api.status[0].url
  description = "Cloud Run API URL"
}

output "frontend_bucket" {
  value       = google_storage_bucket.frontend.name
  description = "Frontend bucket name"
}

output "database_connection_name" {
  value       = google_sql_database_instance.postgres.connection_name
  description = "Cloud SQL connection name"
}
