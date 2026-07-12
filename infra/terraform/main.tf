provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  required_apis = toset([
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each = local.required_apis

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.service_name
  description   = "Imagens da aplicação de otimização de rotas médicas"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

resource "google_service_account" "app" {
  account_id   = var.service_name
  display_name = "Cloud Run - Otimização de Rotas Médicas"

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "openai_api_key" {
  count = var.enable_openai ? 1 : 0

  secret_id = "${var.service_name}-openai-api-key"
  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "openai_accessor" {
  count = var.enable_openai ? 1 : 0

  secret_id = google_secret_manager_secret.openai_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_cloud_run_v2_service" "app" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.app.email
    timeout         = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      env {
        name  = "LLM_PROVIDER"
        value = var.enable_openai ? "openai" : "local"
      }

      env {
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }

      dynamic "env" {
        for_each = var.enable_openai ? [1] : []
        content {
          name = "OPENAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.openai_api_key[0].secret_id
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        initial_delay_seconds = 2
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 12

        http_get {
          path = "/health"
          port = 8080
        }
      }

      liveness_probe {
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 30
        failure_threshold     = 3

        http_get {
          path = "/health"
          port = 8080
        }
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.app,
    google_secret_manager_secret_iam_member.openai_accessor,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
