terraform {
  required_version = ">= 1.7.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "container_image" {
  type = string
}

resource "google_cloud_run_v2_service" "api" {
  name     = "knoema-api"
  location = var.region

  template {
    containers {
      image = var.container_image
      ports {
        container_port = 8000
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }
  }
}

resource "google_sql_database_instance" "postgres" {
  name             = "knoema-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro"
  }
}

resource "google_sql_database" "knoema" {
  name     = "knoema"
  instance = google_sql_database_instance.postgres.name
}

resource "google_redis_instance" "cache" {
  name           = "knoema-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
}

output "cloud_run_uri" {
  value = google_cloud_run_v2_service.api.uri
}
