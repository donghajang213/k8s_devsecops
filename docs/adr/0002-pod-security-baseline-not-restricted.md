# ADR 0002: Pod Security Standards를 "restricted"가 아니라 "baseline"으로

## 상태
승인됨

## 배경
`default` 네임스페이스에 Pod Security Standards를 적용하기로 했다. K8s는 세 단계
(`privileged` < `baseline` < `restricted`)를 제공한다.

## 결정
`enforce: baseline`, `audit`/`warn`은 `restricted`로 설정했다 (실제 차단은 baseline
기준이지만, restricted 기준으로 뭐가 걸리는지는 로그로 계속 확인할 수 있게).

## 근거
공식 `postgres` 이미지의 엔트리포인트 스크립트는 컨테이너 시작 시 **root로 실행되어**
데이터 디렉토리 권한(chown)을 맞춘 뒤, 내부적으로 `gosu`로 `postgres` 유저에게 권한을
넘긴다. `restricted` 표준은 `runAsNonRoot: true`를 강제하는데, 이걸 그대로 켜면
Postgres 공식 이미지의 시작 절차 자체가 막혀서 컨테이너가 못 뜬다.

`baseline`은 이 호환성 문제를 피하면서도, 알려진 주요 권한 상승 경로
(privileged 컨테이너, `hostNetwork`/`hostPID`/`hostIPC`, 위험한 Linux capability,
`hostPath` 볼륨 등)는 그대로 차단한다.

## 적용한 보완책
- `api` 컨테이너는 우리가 직접 만든 이미지라 애초에 non-root(UID 1000)로 구성했으므로,
  이 컨테이너에는 개별적으로 `restricted` 수준의 `securityContext`
  (`runAsNonRoot`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`,
  `seccompProfile: RuntimeDefault`)를 명시적으로 적용했다.
- 즉 네임스페이스 전체는 baseline이 최소 기준이고, 개별 워크로드는 가능한 만큼
  더 엄격하게(api는 restricted 수준으로) 강화하는 방식으로 갔다.

## 트레이드오프
- Postgres 파드 자체는 `restricted` 기준을 다 만족하지 못한다 (컨테이너 자체는 여전히
  postgres 유저로 전환되어 실행되지만, 파드 시작 절차상 pod-level `runAsNonRoot`는 못 켬).
- 커스텀 postgres 이미지를 만들어 root 부트스트랩 로직 없이 처음부터 non-root로 시작하게
  하면 `restricted`까지 갈 수 있으나, 지금 범위(포트폴리오, 시간 제약)에서는 하지 않았다.
