# Terraform으로 GKE 구축하기

GCP 프로젝트 준비(`docs/gcp/default_env.md` 참고)가 끝났다는 전제. Terraform 파일을 역할별로 나눠서 구성한다.

```
terraform/
  versions.tf
  providers.tf
  variables.tf
  main.tf
  terraform.tfvars   # 실제 값, git에는 안 올림
```

## 1. `versions.tf` — Terraform/provider 버전 고정

```hcl
terraform {
  required_version = ">= 1.15"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}
```
버전을 고정하는 이유는 재현성 — 몇 달 뒤 같은 코드로 다시 apply했을 때 provider가 알아서 업데이트되며 동작이 달라지는 걸 막는다.

## 2. `providers.tf` — 어느 프로젝트/리전에 작업할지

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

## 3. `variables.tf` — 값을 하드코딩하지 않고 변수로 분리

```hcl
variable "project_id" {
  type        = string
  description = "GCP 프로젝트 ID"
}

variable "region" {
  type    = string
  default = "asia-northeast3"
}
```
`description`은 사람이 읽는 설명 텍스트다. 실제 값이 아니다 — 실제 값은 `terraform.tfvars`에서 채운다.

## 4. `terraform.tfvars` — 실제 값

```hcl
project_id = "k8s-devsecops-dh"
```
`.gitignore`에 `*.tfvars`를 넣어서 커밋되지 않게 한다 (지금은 project_id 정도라 덜 민감하지만, 나중에 진짜 민감한 값이 들어올 수 있어 습관을 들여둔다).

## 5. `main.tf` — GKE 클러스터 + 노드 풀

```hcl
resource "google_container_cluster" "primary" {
  name     = "k8s-devsecops"
  location = "asia-northeast3-c"   # 리전이 아니라 zone 하나 - 비용 절감

  # 기본 노드 풀은 세부 설정이 제한적이라, 공식 문서가 권장하는 패턴:
  # 만들자마자 기본 풀은 제거하고 별도 node_pool 리소스를 쓴다.
  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"
  cluster    = google_container_cluster.primary.name
  location   = google_container_cluster.primary.location
  node_count = 2

  node_config {
    machine_type = "e2-medium"
    disk_size_gb = 50
  }
}
```

`location`을 리전(`asia-northeast3`)으로 주면 그 리전의 여러 zone에 노드를 분산해서 만들어 노드 수가 최소 3배로 뛴다. zone 하나(`asia-northeast3-c`)로 주면 비용이 훨씬 적다. 학습/포트폴리오 목적이면 zone 클러스터로 충분하다.

## 6. Artifact Registry (Docker 이미지 저장소)

```hcl
resource "google_artifact_registry_repository" "app_repo" {
  location      = "asia-northeast3"
  repository_id = "k8s-devsecops"
  format        = "DOCKER"   # 대문자! "Docker"라고 쓰면 apply 시점에 에러
}
```

## 7. 실행

```
terraform init     # provider 플러그인 다운로드, 아직 실제 리소스는 안 건드림
terraform plan      # 뭘 만들지 미리보기, 역시 실제 리소스는 안 건드림
terraform apply     # 실제로 GCP에 리소스 생성 - 여기서부터 과금 시작
```

## 겪었던 실수: apply 중간에 끊었더니 기본 노드 풀이 안 지워짐

`terraform apply`를 실행하고 GKE 클러스터가 만들어지는 도중(수 분 걸림) 중간에 멈췄더니, 이후 `terraform state list`와 `terraform plan`은 "문제없음"이라고 나오는데 실제 GCP엔 `default-pool`이 남아있는 상태가 됐다.

**원인**: `remove_default_node_pool = true`는 클러스터를 처음 만들 때 "기본 풀을 지워라"는 명령을 한 번 날리는 옵션이지, Terraform이 계속 감시하는 별도 리소스가 아니다. apply가 그 삭제 명령이 실행되기 전에 끊기면, Terraform 입장에서는 "설정대로 다 됐다"고 착각하고 `plan`도 "No changes"라고 답한다 — **Terraform으로는 이 드리프트를 감지도 자동 수정도 못 한다.**

**확인 방법**:
```
gcloud container node-pools list --cluster <클러스터이름> --zone <zone> --project <프로젝트ID>
```
`default-pool`과 우리가 만든 노드 풀이 같이 나오면 이 문제다 (노드 수도 의도한 것보다 많게 나온다).

**해결**: 수동으로 지운다.
```
gcloud container node-pools delete default-pool --cluster <클러스터이름> --zone <zone> --project <프로젝트ID>
```

**교훈**: `terraform apply`처럼 시간이 걸리는 작업은 중간에 끊지 말고 끝까지 기다리는 게 안전하다. 부득이하게 끊었다면 `terraform plan`이 "No changes"라고 해도 안심하지 말고, 클러스터/노드 풀처럼 부분 생성이 가능한 리소스는 실제 클라우드 콘솔/CLI로 한 번 더 교차 확인해야 한다.
