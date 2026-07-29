# k8s_devsecops

정부 지원사업(기업마당, 공공데이터포털) 데이터를 수집·통합해 조회 API로 제공하는
파이프라인을 소재로, DevSecOps/Kubernetes 전 과정을 직접 구축한 포트폴리오.

## 아키텍처

```
기업마당 API ─┐
              ├─► ingest (ETL) ─► PostgreSQL ─► FastAPI(/programs) ─► (조회)
공공데이터포털 ─┘

GitHub push ─► CI(gitleaks/bandit/Trivy) ─► Artifact Registry
                                                    │
                                              ArgoCD가 감시(GitOps)
                                                    ▼
                                        GKE (Postgres + API + 마이그레이션 Job)
                                                    │
                                    Prometheus/Grafana가 관측, NetworkPolicy로 트래픽 통제
                                    시크릿은 GCP Secret Manager ─► External Secrets Operator
```

## 구성 요소

| 영역 | 도구 | 위치 |
|---|---|---|
| 데이터 파이프라인 | Python, FastAPI, SQLAlchemy, Alembic | `src/` |
| 컨테이너화 | Docker, docker-compose(로컬 개발용) | `Dockerfile`, `docker-compose.yml` |
| IaC | Terraform (GKE, Artifact Registry, IAM, Secret Manager, Workload Identity) | `terraform/` |
| K8s 배포 매니페스트 | Deployment, Service, Job, NetworkPolicy, RBAC 등 | `k8s/` |
| CI 보안 게이트 | GitHub Actions + gitleaks(시크릿) + bandit(SAST) + Trivy(이미지 취약점) | `.github/workflows/ci.yml` |
| GitOps 배포 | ArgoCD (자동 동기화 + selfHeal) | `argocd/` |
| 시크릿 관리 | External Secrets Operator + GCP Secret Manager (Workload Identity, 정적 키 없음) | `k8s/secret-store.yaml`, `terraform/secrets.tf` |
| 관측 | Prometheus + Grafana (kube-prometheus-stack) | `observability/` |
| 설계 결정 기록 | ADR | `docs/adr/` |
| 학습 노트 | 초보자가 따라할 수 있는 단계별 가이드 | `docs/{dataengineer,docker,gcp,terraform}/` |

## 로컬에서 실행

```
uv sync
docker compose up -d --build   # db, adminer, api
uv run python -m src.ingest    # 데이터 수집/적재
```

## GKE에 배포

`docs/gcp/default_env.md` → `docs/terraform/default_env.md` 순서로 GCP 프로젝트와
클러스터를 준비한 뒤, `argocd/application.yaml`을 적용하면 이후로는 `k8s/`에 대한
변경이 git push만으로 자동 배포된다.

## 알려진 한계

설계 결정과 그 트레이드오프는 `docs/adr/`에 정리했다. 특히:
- Postgres는 StatefulSet이 아니라 Deployment로 단순화 (`0001`)
- Pod Security Standards는 `restricted`가 아니라 `baseline` (`0002`)
- Vault 대신 External Secrets Operator + GCP Secret Manager (`0003`)
- 이미지 태그가 `:latest` 고정이라 배포 자동화가 완전하지 않음 (`0004`)
