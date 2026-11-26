# SPPS Planner V9.0.0 — Integrated Evolution 개발·검증·인수인계

**기준:** AI_PERFORMANCE_HARDENED (2026-11-09), 통합 개선 (2026-11-10). 앱 버전 **V9.0.0 유지**. Public과 Private는 독립 소스. 이 문서는 신규 기능 범위와 남은 검증을 구분한다.

## 1. 이번에 실제로 구현한 기능

| 분야 | 추가 구현 | 한계/해석 |
|---|---|---|
| Windows 안정성 준비 | Tk 메인 스레드 외 AI 작업, **학습 프로세스 Spawn/Terminate 취소**, 메모리 가용량 preflight(선택 psutil), `multiprocessing.freeze_support()`와 Windows QA 스크립트 | **네이티브 Windows GUI/EXE/Installer는 실제 검증하지 않음**. 파일 읽기 등 일반 I/O 작업은 취소 불가인 daemon thread이며 종료된 창에는 결과를 쓰지 않는다. |
| GUI 스레드 문제 | Python 3.13/Tk에서 이전 창의 GC 소멸자가 워커 스레드에서 실행될 위험 완화를 위해 Tk 메인 스레드에서 이전 garbage 수집 후 I/O worker 기간 동안 자동 GC 일시 제한 | 실제 Windows별 Tcl 버전에서 별도 시험 필요. 중복 작업은 기존 single-flight 정책 유지. |
| 분자 구조 | RDKit **선택형** 구조 검증: **자유 N/C 말단의 일반 L-아미노산 선형 펩타이드** 그래프와 head-to-tail 단일 결합 생성, 독립 평균 MW/분자식 확인 | 보호기·D형·비천연 잔기·분지·Resin은 **원자 구조로 검증하지 않음**. `WITHHELD` 표시. 기존 `mass_balance_v9.py`, `engine.py` 결과가 자동 변경되지 않는다. |
| Auto Plan 3.0 기반 | 검토용 SPPS → 선택적 Cleavage → Head-to-tail → 최종 탈보호 → 분석 단계 초안 및 조건 미입력 Blockers. 제품 유형 변경 시 표시 갱신 | 실제 반응 시간, 촉매·시약 비율을 자동 발명하지 않는다. 실행 권한은 기존 Generate/Apply 흐름에 있고 Lab SOP로 승격되지 않는다. |
| 실험 Excel | 반응 단계, 조건, 보호기 profile, 실제 전환율/수율, HPLC Method, 관측 m/z를 영문/한글 별칭으로 인식. 별도 Process Runs 빈 Excel 템플릿 추가 | 엑셀 시트별 단위·실측값 확인 필요. 관측 m/z는 원본 데이터로 보존하며 이론 분자량과 동일시하지 않는다. |
| AI·ML 비교 | **과정별 분리된 모델**: Coupling conversion, Cyclization yield, Cleavage recovery, Crude yield, Purification recovery. 서열 그룹 분할로 RandomForest/ExtraTrees 비교, 중앙값 baseline보다 열세면 모델 보류. 제품 형태별 자동 파티션 학습 | 기존 최종 yield/purity RandomForest 모델은 별도 유지. ML은 합성 조건을 자동 적용하지 않는다. |
| 불확실성 | 40개 이상의 독립 서열 그룹에서 별도 그룹을 보정 자료로 남겨 **group split conformal 반경** 산출 시도. 그 외에는 holdout 기반 **기술적** 오차 분위수만 기록 | 교환가능성·같은 데이터 생성 분포에 의존; 실제 실험에서 목표 보장, 개별 서열 보장은 아니다. 보정 데이터는 최종 재학습에 섞지 않는다. |
| 데이터 범위 제한 | Cyclic/Linear/Protected 분리, 보호형에는 `protection_profile` 필수, Branch는 정확한 원자 구조가 없어 단계 ML 보류, 새 조건·학습 범위 밖 결과 차단 | 반응별 데이터가 부족하면 거절 메시지를 보여준다. |
| 실험 피드백 | Run ID와 반응 단계에 따른 실제 측정 수치의 별도 요약·기존 Run 연결 현황 | 다른 단계별 수율을 임의로 곱해 최종 수율로 변환하지 않는다. |
| 논문 근거 | 기존 8개 큐레이션된 반응 논문의 source ID·서지·링크를 로컬 검색해 Auto Plan JSON과 GUI에 표시 | 자동 웹 검색/생성형 AI/논문 전문 분석은 구현하지 않음. 문헌 적용을 보증된 SOP로 표시하지 않음. |

## 2. Excel 사용법

1. Project Manager → **Auto Plan (Optional)** → **AI · Import Excel / CSV...**
2. **Create reaction-stage template** 버튼으로 `Process_Runs`가 빈 Excel 파일 생성.
3. `Sequence`, `Run ID`, `Product path`, `Reaction step`, 정확한 `Reaction method`, 실제 결과를 기록. `Scale`, `Loading`, `Resin`, `Coupling`도 기록.
4. 보호형이면 `Protecting groups`에 사용한 상태를 정확히 기록. 예: `1:S(tBu);3:S(tBu)` (예시는 형식이며 실제 실험으로 검증해야 한다).
5. 파일 선택 → 헤더 자동 매핑 검토 → **Stage reviewed file / Next** (여러 파일일 때) → **Audit data quality** → 승인 후 Save.
6. ML target에서 `cyclization_yield_percent` 등 선택 → **Train local AI**. 한 대상에 제품 형태가 섞여 있어도 **자동으로 다른 하위 모델에 분할**한다. 학습 중 **Cancel training**은 별도 학습 프로세스를 중지한다.
7. **Compare current peptide**로 동일한 제품 형태·시약·보호기 상태 등에 일치하는 참고 예측이 있는지 확인. 결과는 실험 SOP에 자동 적용되지 않는다.

### 지원 데이터 필드

`sequence`, `run_id`, `product_path`, `reaction_step`, `reaction_method`, `cleavage_method`, `protection_profile`, `reaction_time_h`, `reaction_concentration_mm`, `scale_mmol`, `loading_mmol_g`, `resin`, `chemistry`, `actual_yield_percent`, `actual_purity_percent`, `coupling_conversion_percent`, `cyclization_yield_percent`, `cleavage_recovery_percent`, `crude_yield_percent`, `purification_recovery_percent`, `hplc_method`, `observed_mz`.

동일 Run ID의 서로 다른 `reaction_step`은 별도 기록으로 저장 가능하다. 동일 Run ID·단계에 서로 상충하는 결과가 있으면 학습을 보류한다. 중복 기록을 자동 삭제하지 않는다.

## 3. Auto Plan 및 화학 데이터

- `structure_crosscheck_v9.py`: 일반 L-아미노산 자유 말단만 RDKit으로 계산. 분자식·평균 MW는 계산해도 **분석 장비 측정값이 아니다**. 보호형 product MW는 기존 `mass_balance_v9` 근거를 유지하고 독립적으로 검증했다고 주장하지 않는다.
- `auto_plan_evolution_v9.py`: 각 단계의 mass state를 기존 계산과 연결. **Blocker가 있다고 기존 Generate를 몰래 바꾸지 않음**. 반응법의 자동 확정은 지원하지 않는다.
- `research_assistant_v9.py`: 8건의 문헌을 로컬 검색. 원문 링크만 제공하고 실험 최적 반응법을 생성하지 않는다.
- 과정별 AI는 보호기/결합 정보 없이 예측하면 부적절할 수 있어, 원자 구조를 알 수 없는 Branch와 표기가 불충분한 보호형 실험을 무조건 예측하지 않는다.

## 4. 소스 구조와 배포

**새 모듈:**

- `apps/spps_planner_app/spps_planner/structure_crosscheck_v9.py`
- `apps/spps_planner_app/spps_planner/research_assistant_v9.py`
- `suite_gui/auto_plan_evolution_v9.py`
- `suite_gui/process_ai_v9.py`
- `suite_gui/experiment_feedback_v9.py`
- `tests/test_v9_full_evolution_additions.py`
- `tools/windows_acceptance_v9.py`
- `requirements-rdkit-optional.txt`

**수정 모듈:** `suite_gui/auto_plan_option_v9.py`, `suite_gui/ai_excel_core_v9.py`, `suite_gui/ai_excel_dialog_v9.py`, `suite_gui/ai_background_v9.py`, `main_launcher.py`, 사용자 README, Release Notes.

**보존:** `apps/spps_planner_app/spps_planner/engine.py`, 기존 Step1/Step2, Plan/Materials/Checklist/Workup, 단일 `INSTALL_BUILD_TOOLS_AND_BUILD.bat`, Public/Private 데이터 경계, 내부 데이터 스키마 `SPPS data v6.0.0`.

### 설치 (개발 소스)

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip install -r requirements-rdkit-optional.txt
python main_launcher.py --self-test
python main_launcher.py
```

`rdkit`는 선택 사항이다. 설치하지 않아도 기본 합성 계산과 AI가 실행되어야 하며, 구조 독립 교차검증만 `OPTIONAL_RDKIT_NOT_INSTALLED`로 표시한다. `psutil`은 메모리 preflight에만 선택적으로 사용한다.

### Windows 네이티브 검증

```bat
python tools\windows_acceptance_v9.py
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

위 검증 스크립트는 Windows에서 `--self-test` 및 Tk 메인창 생성 결과를 JSON 파일에 기록한다. **설치/업그레이드/제거·장시간 성능은 별도 수동 시험**이다. Linux에서 실행하면 `NOT_TESTED_NOT_WINDOWS`로 기록한다.

## 5. 테스트 및 과학적 한계

정적 검사, Python 컴파일, 신규 기능 14건, Linux Xvfb/Tk GUI, 소스 회귀시험과 Windows 네이티브 설치 검사는 독립 상태로 기록한다. 회귀 테스트의 PASS는 합성 실패율·수율 예측 정확도의 실험적 검증과 다르다. 모델 성능 목표(외부 검증 MAE 향상)는 **실제 기록 데이터 없이 달성 여부를 말할 수 없다**.

### 아직 완성하지 않은 범위

- RDKit 전 원자 보호기/D-형/Branch/Thioether/Click/Disulfide 구조 그래프와 원자 단위 반응 매핑
- AI가 논문을 실시간 검색하고 생성형 모델로 문헌을 심층 추론하는 서비스
- 대용량 Excel 1만 행 및 Windows 10/11 네이티브 장시간 메모리·스크롤·취소·Installer 실측 시험
- 화학적으로 검증된 Cyclic/Branch 최적 반응 추천, 실제 배치의 외부 수득률 예측 검증

이 항목을 이미 완성했다고 README 또는 GitHub Release에서 주장하면 안 된다.

## 6. 관련 공개 자료

- RDKit Python 시작 안내: https://www.rdkit.org/docs/GettingStartedInPython.html
- scikit-learn GroupShuffleSplit: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html
- scikit-learn ExtraTreesRegressor: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html
- openpyxl optimized modes: https://openpyxl.readthedocs.io/en/stable/optimized.html
- 반응 근거 8건: `apps/spps_planner_app/spps_planner/reaction_evidence_v9.py`

본 문서는 소스 기반 소프트웨어 개발·검증 기록이며 의료·실험 SOP 인증 문서가 아니다.
