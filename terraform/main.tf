resource "google_container_cluster" "primary" {
  name     = "k8s-devsecops"                    # 클러스터 이름 (예: "k8s-devsecops")
  location = "asia-northeast3-c"                    # 리전이 아니라 zone 하나로 (예: "asia-northeast3-a") - 비용 절감

  # 기본 노드 풀은 세부 설정이 제한적이라 공식 문서가 권장하는 패턴:
  # 기본 노드 풀은 만들자마자 제거하고, 아래 별도 node_pool 리소스를 쓴다
  remove_default_node_pool = true
  initial_node_count       = 1

  # Workload Identity: K8s ServiceAccount가 GCP 서비스 계정을 대행할 수 있게 함
  # (External Secrets Operator가 Secret Manager를 읽을 때, 정적 키 없이 인증하기 위해 필요)
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"                  # 노드 풀 이름
  cluster    = google_container_cluster.primary.name
  location   = google_container_cluster.primary.location
  node_count = 2                    # 1~2개로 (크레딧 아끼기)

  node_config {
    machine_type = "e2-medium"              # e2-small 또는 e2-medium
    disk_size_gb = 50                # 기본값보다 줄여도 됨 (예: 30)
  }
}

resource "google_artifact_registry_repository" "app_repo" {
    location = "asia-northeast3"
    repository_id = "k8s-devsecops"
    format = "DOCKER"
}
