variable "project_id" {
  description = "ID do projeto Google Cloud que receberá a aplicação."
  type        = string
}

variable "region" {
  description = "Região do Artifact Registry e Cloud Run."
  type        = string
  default     = "southamerica-east1"
}

variable "service_name" {
  description = "Nome dos recursos da aplicação."
  type        = string
  default     = "rotas-medicas"
}

variable "container_image" {
  description = "Imagem imutável publicada no Artifact Registry, incluindo a tag."
  type        = string
}

variable "allow_unauthenticated" {
  description = "Expõe a interface publicamente quando verdadeiro."
  type        = bool
  default     = true
}

variable "enable_openai" {
  description = "Injeta o segredo OPENAI_API_KEY e ativa o provedor OpenAI."
  type        = bool
  default     = false
}

variable "openai_model" {
  description = "Modelo usado quando a integração OpenAI estiver ativa."
  type        = string
  default     = "gpt-5.6"
}

variable "max_instances" {
  description = "Limite de instâncias para controlar custos."
  type        = number
  default     = 2

  validation {
    condition     = var.max_instances >= 1
    error_message = "max_instances deve ser pelo menos 1."
  }
}
