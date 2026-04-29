variable "namespace" {
  type    = string
  default = "ai-sql-analyst"
}

variable "image" {
  type    = string
  default = "ghcr.io/evanriley00/ai-sql-analyst:latest"
}

variable "api_keys" {
  type      = string
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "postgres_password" {
  type      = string
  sensitive = true
}
