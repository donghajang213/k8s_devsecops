data "google_project" "current" {}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id         = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  # 이 저장소(repo)에서 실행되는 워크플로만 이 provider로 인증 허용
  attribute_condition = "assertion.repository == \"donghajang213/k8s_devsecops\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "ci_deployer" {
  account_id   = "ci-deployer"
  display_name = "GitHub Actions CI - image push"
}

# Artifact Registry에 이미지를 푸시할 수 있는 권한만 부여 (최소 권한)
resource "google_project_iam_member" "ci_deployer_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.ci_deployer.email}"
}

# GitHub Actions(WIF)가 이 서비스 계정을 "대행"할 수 있게 허용
resource "google_service_account_iam_member" "ci_deployer_wif_binding" {
  service_account_id = google_service_account.ci_deployer.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/donghajang213/k8s_devsecops"
}

output "wif_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "ci_deployer_email" {
  value = google_service_account.ci_deployer.email
}
