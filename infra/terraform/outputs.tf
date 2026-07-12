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

output "openai_secret_id" {
  description = "Segredo a preencher fora do Terraform quando a OpenAI estiver ativa."
  value = (
    var.enable_openai
    ? google_secret_manager_secret.openai_api_key[0].secret_id
    : null
  )
}
