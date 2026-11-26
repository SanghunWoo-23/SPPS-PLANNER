# SPPS Planner V9.0.0 — GitHub 공개 절차와 기준

> 기준: Public **development source**. 실제 Windows EXE·Installer 성공, 임상/실험적 결과,
> 독립 데이터 AI 성능을 검증한 정식 릴리스라고 표시하지 않는다.

## 1. GitHub에 올릴 구성

- Public 소스만 업로드한다. `PRIVATE` ZIP, 내부 실험 시드, 로컬 DB/모델,
  기업 프로젝트 파일, 비밀번호/API Key는 포함하지 않는다.
- 공개 소스 라이선스는 현재 프로젝트의 **custom non-commercial academic citation license**이며
  OSI 승인 오픈소스 라이선스가 아니다. 변경되지 않았다.
- GitHub `SanghunWoo-23/SPPS-PLANNER`의 기존 기본 브랜치는 `V8.0.0`이었다.
  해당 코드를 덮어쓰지 말고 `V9.0.0-development` 개발 브랜치를 만든다.

## 2. 권장 업로드 방식

1. Public ZIP을 압축 해제한다.
2. 로컬 Git 작업 폴더에서 `V8.0.0` 브랜치의 변경사항을 확인하고,
   `V9.0.0-development` 브랜치를 만들어 Public **소스의 내부 파일들**을 루트에 배치한다.
   ZIP 파일 한 개만 저장소에 커밋하지 않는다.
3. `python tools/github_release_preflight_v9.py --strict`를 실행한다.
4. `python -m pytest -q tests/test_v9_github_public_preflight.py`와 프로젝트 회귀시험을 실행한다.
5. Commit과 Pull Request 후 Actions의 `CI`와 `Public Source Release Preflight` 결과를 확인한다.
6. 성공한 경우에만 GitHub Release 초안 작성 후 **Pre-release**로 공개한다.

## 3. 사전 검증과 다운로드용 소스 ZIP

```bash
python tools/github_release_preflight_v9.py --strict
python tools/build_github_source_release_v9.py --output ../SPPS_Planner_V9.0.0_PUBLIC_SOURCE.zip
python -m pytest -q tests/test_v9_github_public_preflight.py
```

- 사전 검사는 개인정보·로컬 DB·실험 시드/모델·버전 불일치·SHA-256 변경을 검사한다.
- 테스트 중 새 소스 파일을 추가한 유지보수자는 검토 후
  `python tools/github_release_preflight_v9.py --write-manifest --strict`로 Manifest를 갱신한다.
- CI는 다운로드용 **소스 ZIP과 사전검사 리포트를 Actions Artifact**로만 저장한다.
  GitHub Release를 자동 공개하거나 기존 브랜치를 업데이트하지 않는다.
- Windows 네이티브 CI의 실제 성공 기록이 확보되기 전에는 성공을 주장하지 않는다.

## 4. 차단해야 할 사항

- Private ZIP의 GitHub 업로드
- 출처를 모르는 모델 직렬화 파일 업로드 또는 실행
- 사용자 프로젝트·보호형 펩타이드 정보·실험 결과 자동 공개
- 근거 없는 고리화 수율·순도 예측 또는 검증된 SOP라는 표현
- Windows 설치 성공 로그 없이 `Windows Verified` 표기

## 5. 외부 저작물과 인용

독립 구현 및 공식 문서 참조를 원칙으로 하고, 외부 프로젝트 코드를 가져올 경우
원본 라이선스를 확인하여 필요한 저작권 표시·고지를 포함한다.
`CITATION.cff`의 현재 버전은 9.0.0으로 맞추었고 소스 라이선스의 인용 예시도 갱신했다.
