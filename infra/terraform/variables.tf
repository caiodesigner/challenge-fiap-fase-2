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

variable "llm_provider" {
  description = "Provedor de linguagem no Cloud Run: local ou ollama."
  type        = string
  default     = "local"

  validation {
    condition     = contains(["local", "ollama"], var.llm_provider)
    error_message = "llm_provider deve ser local ou ollama."
  }
}

variable "ollama_host" {
  description = "URL de um Ollama acessível pelo Cloud Run quando habilitado."
  type        = string
  default     = "http://127.0.0.1:11434"
}

variable "ollama_model" {
  description = "Modelo pré-treinado disponível no serviço Ollama."
  type        = string
  default     = "qwen2.5:1.5b"
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
