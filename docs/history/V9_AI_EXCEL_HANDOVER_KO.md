# SPPS Planner V9.0.0 — AI Auto Plan / Excel ML 개발 인수인계

> **2026-11-08 이후 코드 갱신 알림:** 이 문서는 V9 AI·Excel 초기 구현 당시 기록이다. 현재 특징량·3회 그룹 검증·원본 무결성·Topology 예측 보류 사항은 [V9_AI_REFACTOR_HARDENING_KO.md](V9_AI_REFACTOR_HARDENING_KO.md)를 우선한다.

**기준:** 2026-11-08 / Windows 10·11 목표 / Public·Private 분리 / **앱 버전 V9.0.0 유지**

## 1. 이번에 구현한 사항

1. **외부 Excel/CSV → 자동 열 매핑**: `.xlsx`, `.csv`, `.tsv`, `.txt` 지원. 한글/영문 header alias, 첫 9행 중 헤더 자동 탐색, 여러 Excel 시트 선택, 열 매핑 변경, 12행 미리보기.
2. **단위 정리와 입력 검증**: `actual_yield_percent`, `actual_purity_percent`, `sequence`, `scale_mmol`, `loading_mmol_g`, `resin`, `chemistry`, `run_id`. Excel native percent formatting(0.75 표시 75%)은 감지 후 0–100 변환(사용자가 해제 가능). 측정치 >100% 또는 <0%는 제외/NaN 처리, 잘못된 서열/수치의 학습은 제한. 데이터 원본에 대하여 읽기 전용 동작.
3. **검토와 저장 분리**: Choose → Check & clean → 동의 → Save reviewed data → Train 순서. 매핑이나 % 표기 옵션을 바꾸면 반드시 다시 Preview. 현재 프로젝트나 `actual_runs.csv`에 외부 결과를 몰래 추가하지 않음. 승인된 데이터셋 한 개를 각 별도 사용자 프로필의 JSON으로 원자 저장하며, 다음 파일 저장 시 이전 데이터를 명시적으로 교체.
4. **로컬 감독학습(RandomForestRegressor)**: 수득률 또는 순도 목표 선택. 서열 특성(길이, Cys/Asp/Pro/Gly 수), Scale, Loading, Resin, Coupling을 입력 특징으로 사용. `GroupShuffleSplit`으로 동일 서열이 학습/홀드아웃 동시에 포함되지 않게 분리. 최소 24개 실측 레코드·6개 독립 서열·복수 결과와 충분한 Scale/Loading 유효 수치를 요구. 중앙값 baseline보다 좋지 않으면 모델 보류. `joblib` 모델은 체크섬 일치하는 자체 생성 프로필 파일에만 사용.
5. **Auto Plan에 연결**: `AI · Import Excel / CSV...` 버튼으로 열어 유사 실험 최대 3건 비교. 검증을 통과한 로컬 모델이 있는 경우 탐색적 수득률/순도 % 표시. 학습 데이터 범위 밖(서열 길이·Scale·Loading·레진·Coupling)이면 OOD 처리. 사용자가 Attach evidence를 눌러야 미승인 Auto Plan 초안에 포함. Export JSON에 `ai_evidence`, Generate 성공 시 프로젝트 아이템에 `v9_ai_evidence` 저장. Generate 실패 시 이전 값 복원.
6. **Private/Public 보호**: 기존 profile 기본 폴더 유지 (`SPPS_Planner_PRIVATE` vs `SPPS_Planner_PUBLIC`). 외부 파일·모델은 소스 ZIP에 포함되지 않음. 인터넷/LLM API 호출 없음.
7. **EXE 패키징**: `SPPS_Planner.spec` hiddenimports에 AI Core/Dialog/Auto Plan 명시. 단일 BAT 기존 유지.

## 2. 변경 파일

- `suite_gui/ai_excel_core_v9.py` 신규 — Excel/CSV 해석·자동 매핑·정규화·서열 특징화·학습·OOD/모델 검사·유사 실험 검색
- `suite_gui/ai_excel_dialog_v9.py` 신규 — Tkinter 가져오기/Preview/승인/Train/Compare/Attach 창
- `suite_gui/auto_plan_option_v9.py` 수정 — Auto Plan AI 버튼·근거 연결·JSON export·저장 rollback
- `suite_gui/modules/ml_lab_panel.py` 수정 — ML Lab에서도 Excel AI Import 접근
- `SPPS_Planner.spec` 수정 — 런타임 hiddenimports 명시
- `tests/test_v9_ai_excel_import.py` 신규 — CSV/TSV/XLSX, % 스타일, 한글 header, 구문/잘못된 값, 모델 학습, OOD, 데이터 변경, 파일 무결성, Tk GUI
- `README.md`, `README_KO.md`, `README_V9_DEVELOPMENT.md`, `docs/V9_AI_EXCEL_ASSISTANT_EN.md`, `_KO.md` 수정/추가

## 3. 화학 엔진 변경 여부

`apps/spps_planner_app/spps_planner/engine.py`는 이번 변경으로 수정하지 않았습니다. AI는 **실험 근거와 결과의 보조 분석**이며, SPPS 합성 조건·보호기·Cyclization 시약량·사용자 승인 상태에 대한 독립된 결정권이 없습니다.

## 4. 데이터 포맷 및 개발 정책

- 기존 V9 프로젝트 스키마/`SPPS data v6.0.0` 식별자 임의 수정 금지.
- AI 로컬 데이터: `user_data_dir()/ai_excel_v9/ai_excel_reviewed_v9.json` (개별 Public/Private 프로필)
- AI 모델: `user_models_dir()/ai_excel_v9/ai_excel_(yield|purity)_v9.joblib` 및 `.json` 메타데이터
- 기본 프로필은 각각 다르지만 사용자가 직접 다른 프로필 경로로 복사할 수 있음. Public GitHub 배포 전에 ZIP 내부에 개인/회사 실험기록·모델이 없는지 추가 검사할 것.
- 엑셀 `.xls`/암호화 문서/복잡한 헤더는 미지원. 하나의 원본 파일을 승인하면 기존 외부 AI 데이터셋을 덮어씀. 여러 파일 합치기는 후속 작업.
- 파일 용량 12 MB·20,000행·70열로 제한. 외부 데이터는 실행하지 않고 읽기·정규화·로컬 저장만 하며, 임의 `.joblib` 가져오기는 지원하지 않음.
- 모델은 무작위 홀드아웃 한 번에 근거한 **탐색적 도구**. 수득률의 실제 예측 신뢰도, 실험 최적 조건, 계열 외 일반화 또는 제약된 Cyclization 반응 성능을 보장하지 않음.

## 5. 실행·검증

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python main_launcher.py --self-test
python main_launcher.py
python -m pytest -q tests/test_v9_ai_excel_import.py
python -m pytest -q
python tools\verify_windows_release.py
```

실행 환경: Linux Python / Tk Xvfb GUI 시험, 전체 pytest / 정적 Windows 배포 검사. **Windows 실제 실행 파일 생성·설치·업그레이드·제거와 GUI 실사용 시험은 미검증**. 테스트 수치는 최종 리포트 참조. `--self-test` 통과는 실제 실험 조건 검증을 의미하지 않음.

## 6. 후속 개선 권장

- 여러 엑셀 파일의 안전한 병합(중복 Run ID·서열·날짜 감지)과 데이터 품질 진단 UI.
- 반복 실험 단위/배치/LOT 누출을 방지하는 더욱 엄격한 그룹 분리, K-fold grouped 평가, 외부 전향적 데이터 검증.
- 합성/정제 수득률 분리, Cyclic vs Linear/Protected 상태 별도 타깃, 실제 과학·분석 특성 추출.
- Windows EXE/Installer 실환경 테스트 후 릴리스 확정. 배포 시 `Public`만 GitHub 업로드.
