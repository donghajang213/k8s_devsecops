# GCP 프로젝트 초기 세팅 (GKE용)

Terraform으로 GKE를 다루기 전에, GCP 쪽에서 미리 준비해둬야 하는 것들. 여러 프로젝트를 동시에 다룰 경우를 대비해 "다른 프로젝트와 안 섞이게" 하는 데 초점을 맞췄다.

## 1. 새 프로젝트 생성

```
gcloud projects create k8s-devsecops-<본인이니셜/랜덤숫자> --name="k8s-devsecops"
```

프로젝트 ID는 전 세계에서 유일해야 해서, 흔한 이름만 쓰면 이미 누가 쓰고 있을 확률이 높다. 뒤에 이니셜이나 숫자를 붙인다.

**주의**: 이후 모든 명령에서 쓰는 "프로젝트 ID"는 이 단계에서 만든 문자열(예: `k8s-devsecops-dh`)이다. `gcloud projects list`를 치면 옆에 `PROJECT_NUMBER`라는 숫자 컬럼도 같이 나오는데, **이건 다른 값이다.** Terraform이나 대부분의 gcloud 명령은 프로젝트 ID(문자열)를 기대하므로, 숫자를 잘못 복사해서 넣으면 `gcloud config set project`는 에러 없이 통과되지만 이후 단계(Application Default Credentials의 quota project 등)에서 어긋난다. 아래처럼 확인하면서 진행:

```
gcloud config list
```
`project` 항목이 숫자가 아니라 `k8s-devsecops-dh` 같은 문자열인지 확인.

## 2. 결제 계정 연결

GKE API는 결제 계정이 연결돼 있지 않으면 활성화가 안 된다.

```
gcloud billing accounts list
gcloud billing projects link <프로젝트ID> --billing-account=<위에서 나온 계정ID>
```

## 3. 프로젝트 전용 gcloud 설정(config) 새로 만들기

여러 프로젝트를 오가며 작업할 때, `gcloud config set project`로 매번 전환하면 실수로 엉뚱한 프로젝트에 리소스를 만들 위험이 있다. 프로젝트별로 "설정 묶음(configuration)"을 따로 만들어두면 `gcloud config configurations activate <이름>`으로 통째로 전환할 수 있다.

```
gcloud config configurations create k8s-devsecops
gcloud config set project <프로젝트ID>
gcloud config set account <본인 구글 계정>
```

## 4. 필요한 API 활성화

```
gcloud services enable container.googleapis.com compute.googleapis.com artifactregistry.googleapis.com
```
- `container.googleapis.com` — GKE(Kubernetes Engine)
- `compute.googleapis.com` — Compute Engine (GKE 노드가 결국 VM이라 필요)
- `artifactregistry.googleapis.com` — Docker 이미지 저장소

## 5. Application Default Credentials(ADC) 확인

Terraform은 보통 gcloud 로그인 자격증명(ADC)을 그대로 사용한다. 이게 없거나 quota project가 안 맞으면 나중에 API 호출이 예상과 다르게 과금되거나 실패할 수 있다.

```
gcloud auth application-default print-access-token   # 있는지 확인, 없으면:
gcloud auth application-default login

gcloud auth application-default set-quota-project <프로젝트ID>
```

`project` 설정을 바꾼 직후(2번 참고)라면 `Your active project does not match the quota project...` 경고가 뜰 수 있는데, 마지막 명령으로 맞춰준다.

## 겪었던 실수

- **콘솔(웹사이트)에 프로젝트가 안 보임**: `gcloud projects list`엔 나오는데 GCP 콘솔 화면엔 안 보이는 경우가 있었다. 원인은 "조직(organization)"이 없는 개인 계정이라 콘솔의 프로젝트 선택기가 기본적으로 필터링해서 보여주기 때문 — 프로젝트 선택 드롭다운에서 직접 검색하면 나온다. CLI가 정상이면 콘솔 화면 문제는 무시하고 진행해도 된다.
