# ADR 0003: 시크릿 관리는 Vault가 아니라 External Secrets Operator + GCP Secret Manager

## 상태
승인됨

## 배경
킥오프 때 시크릿 관리 후보로 HashiCorp Vault와 K8s External Secrets(+ GCP Secret
Manager) 두 가지를 놓고 저울질했다.

## 결정
External Secrets Operator(ESO) + GCP Secret Manager로 갔다.

## 근거
- Vault는 자체 클러스터를 띄우고 초기화(unseal), 인증 방식(K8s auth method 등) 설정까지
  직접 운영해야 하는 부담이 크다. GCP 크레딧/기간이 14일로 제한된 상황에서, Vault 자체를
  안정적으로 운영하는 데 시간을 쓰는 것보다 다른 phase(ArgoCD, 하드닝, 관측)에 시간을
  쓰는 게 낫다고 판단했다.
- GCP를 이미 쓰고 있으므로 Secret Manager는 추가 인프라 없이 바로 쓸 수 있다.
- GKE의 Workload Identity로 ESO가 정적 키 없이 GCP Secret Manager를 읽게 구성했다
  (`terraform/secrets.tf`) — Vault 없이도 "시크릿이 코드/git에 평문으로 없다"는
  핵심 목표는 동일하게 달성된다.

## 결과
- `k8s/secret-store.yaml`의 `ClusterSecretStore` + `ExternalSecret`이 DB 자격증명을
  `db-credentials`라는 K8s Secret으로 동기화한다. 애플리케이션 매니페스트
  (`postgres.yaml`, `api.yaml`, `migrate-job.yaml`)는 이 Secret 이름만 참조하므로,
  나중에 Vault로 바꾸더라도 애플리케이션 쪽 변경은 없다.

## 트레이드오프
- Vault가 제공하는 동적 시크릿(dynamic secrets), 세밀한 정책 언어, 멀티클라우드 통합 같은
  고급 기능은 이번엔 다루지 못했다 — 이건 "Vault를 몰라서"가 아니라 "이번 스코프에서는
  GCP Secret Manager로 충분하고, Vault 운영 자체가 이번 프로젝트의 핵심 학습 목표는
  아니었다"는 의도적 범위 조정이다.
