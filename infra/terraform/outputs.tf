output "application_url" {
  description = "URL HTTPS da aplicação no Cloud Run."
  value       = google_cloud_run_v2_service.app.uri
}

output "artifact_registry_repository" {
  description = "Repositório usado para publicar imagens Docker."
  value       = google_artifact_registry_repository.app.name
}

output "runtime_service_account" {
  description = "Conta de serviço de menor privilégio usada pela aplicação."
  value       = google_service_account.app.email
}
