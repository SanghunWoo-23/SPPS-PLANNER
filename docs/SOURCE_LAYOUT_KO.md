# SPPS Planner V9.0.0 — 소스 파일 구조

다음 경로는 실행·Import 호환성 때문에 유지합니다. 실험 데이터는 패키지 안에
자동 저장하는 것이 아니라 사용자의 로컬 프로젝트 경로로 분리해야 합니다.

| 경로 | 기능 |
| --- | --- |
| `main_launcher.py` | 단일 진입점, 자체 점검 |
| `suite_gui/` | Tkinter 창, Auto Plan, Excel/AI, 실험 결과 패널 |
| `apps/spps_planner_app/` | SPPS 계산·화학 검증 및 로컬 데이터 인터페이스 |
| `peptiforg_core/` | 공유 코어 호환 계층 |
| `assets/` | 프로그램 아이콘 |
| `installer/`, `*.spec`, `*.bat` | Windows 빌드 입력(사전 빌드된 EXE가 아님) |
| `tests/` | 회귀·기능·배포 검사 |
| `tools/` | 검증·CLI·배포 지원 스크립트 |
| `docs/` | 현재 매뉴얼·가이드·레퍼런스 |
| `docs/history/` | 과거 개발 단계 기록, 현재 기능 정의에 사용 금지 |
| `.github/` | GitHub 워크플로우 및 이슈 템플릿 |
| `SOURCE_MANIFEST.sha256` | 파일별 SHA-256(Manifest 자체 제외) |

## 공개·실행 구분

- **PUBLIC:** GitHub 공개 후보; 실험 시드·로컬 데이터·개인 학습 모델 제외.
- **PRIVATE:** 내부 전용; 회사·실험 정보가 들어갈 수 있으므로 GitHub에 올리지 않음.
- 릴리스 ZIP은 **소스**이며 Windows EXE/Installer가 아닙니다.
- 과거 문서를 숨기거나 삭제하지 않고 `docs/history/`에 보존합니다.

## 검사 명령

```bash
python main_launcher.py --self-test
python tools/audit_repository_layout_v9.py
python -m pytest -q tests/test_v9_source_layout.py
```

Public GitHub 사전검사: `python tools/github_release_preflight_v9.py --strict`
