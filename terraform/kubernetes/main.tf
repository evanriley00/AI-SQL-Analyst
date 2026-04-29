provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_secret" "app" {
  metadata {
    name      = "ai-sql-analyst-secrets"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  data = {
    AI_SQL_ANALYST_API_KEYS = var.api_keys
    OPENAI_API_KEY          = var.openai_api_key
    POSTGRES_PASSWORD       = var.postgres_password
  }
}

resource "kubernetes_config_map" "app" {
  metadata {
    name      = "ai-sql-analyst-config"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  data = {
    AI_SQL_ANALYST_APP_NAME         = "AI SQL Analyst"
    AI_SQL_ANALYST_DATABASE_BACKEND = "postgres"
    AI_SQL_ANALYST_POSTGRES_DSN     = "postgresql://ai_sql:${var.postgres_password}@ai-sql-analyst-postgres:5432/ai_sql_analyst"
    AI_SQL_ANALYST_QUERY_LOG_PATH   = "/app/data/query_log.jsonl"
    AI_SQL_ANALYST_MAX_QUERY_ROWS   = "100"
    AI_SQL_ANALYST_BROWSER_API_KEY  = "dev-api-key"
  }
}

resource "kubernetes_service" "postgres" {
  metadata {
    name      = "ai-sql-analyst-postgres"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    selector = {
      app = "ai-sql-analyst-postgres"
    }

    port {
      name        = "postgres"
      port        = 5432
      target_port = 5432
    }
  }
}

resource "kubernetes_stateful_set" "postgres" {
  metadata {
    name      = "ai-sql-analyst-postgres"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    service_name = kubernetes_service.postgres.metadata[0].name
    replicas     = 1

    selector {
      match_labels = {
        app = "ai-sql-analyst-postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-sql-analyst-postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:16-alpine"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_DB"
            value = "ai_sql_analyst"
          }

          env {
            name  = "POSTGRES_USER"
            value = "ai_sql"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.app.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }

          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
          }
        }
      }
    }

    volume_claim_template {
      metadata {
        name = "postgres-data"
      }

      spec {
        access_modes = ["ReadWriteOnce"]

        resources {
          requests = {
            storage = "1Gi"
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "ai-sql-analyst-api"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "ai-sql-analyst-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-sql-analyst-api"
        }
      }

      spec {
        container {
          name  = "api"
          image = var.image

          port {
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.app.metadata[0].name
            }
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 10
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 20
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api" {
  metadata {
    name      = "ai-sql-analyst-api"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    selector = {
      app = "ai-sql-analyst-api"
    }

    port {
      port        = 80
      target_port = 8000
    }
  }
}
