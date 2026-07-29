# --- Secret Manager: DB 자격증명 ---
resource "google_secret_manager_secret" "db_user" {
  secret_id = "db-user"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_user" {
  secret      = google_secret_manager_secret.db_user.id
  secret_data = var.db_user
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "db-name"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_name" {
  secret      = google_secret_manager_secret.db_name.id
  secret_data = var.db_name
}

# --- External Secrets Operator가 Secret Manager를 읽을 때 쓸 GCP 서비스 계정 ---
resource "google_service_account" "external_secrets" {
  account_id   = "external-secrets"
  display_name = "External Secrets Operator"
}

resource "google_project_iam_member" "external_secrets_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.external_secrets.email}"
}

# K8s ServiceAccount(external-secrets 네임스페이스의 external-secrets SA)가
# 이 GCP 서비스 계정을 Workload Identity로 대행할 수 있게 허용
resource "google_service_account_iam_member" "external_secrets_wi_binding" {
  service_account_id = google_service_account.external_secrets.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "serviceAccount:${var.project_id}.svc.id.goog[external-secrets/external-secrets-sa]"
}

output "external_secrets_gcp_sa" {
  value = google_service_account.external_secrets.email
}
