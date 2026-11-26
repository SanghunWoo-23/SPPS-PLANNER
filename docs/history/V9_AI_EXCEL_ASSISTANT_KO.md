# SPPS Planner V9.0.0 — Auto Plan AI + Excel/CSV Assistant

## 기능 범위

이 기능은 인터넷/API 연결이 필요 없는 **로컬 ML 보조 기능**입니다. ChatGPT 또는 외부 LLM을 앱 내부에서 호출하는 기능은 아닙니다. 기존 SPPS 화학 계산 엔진과 Generate/Apply Change의 계산 권한은 그대로 유지합니다.

**목표:** 실험자가 엑셀·CSV를 파일 선택으로 넣고, 열 이름을 자동 인식·검토한 뒤, 로컬에서 유사 실험을 비교하거나 수득률/순도 예측 모델을 학습하여 **Auto Plan 검토 근거로 첨부**할 수 있도록 합니다.

## 사용법

1. **Project Manager → Auto Plan (Optional) → AI · Import Excel / CSV...** 를 선택합니다. 일부 GUI 레이아웃에서는 **ML Lab → Import Excel / CSV (AI)**에서도 열 수 있습니다.
2. **1. Choose Excel / CSV**: `.xlsx`, `.csv`, `.tsv`, `.txt` 중 하나를 고릅니다. `.xls`는 사전에 `.xlsx`로 변환합니다. 12 MB 이하, 최대 20,000행·70열의 파일을 권장합니다.
3. Excel은 **워크시트 선택**을 할 수 있습니다. 1~9번째 행에서 표 머리글을 추정하며, 한국어/영문 열 이름을 자동으로 인식합니다.
4. **2. Check & clean**: 매핑이 틀렸다면 각 열의 콤보박스에서 원본 열을 선택합니다. 데이터 미리보기의 서열·측정 수득률·측정 순도를 검토합니다. 이때 아직 데이터 저장·학습은 하지 않습니다.
5. 엑셀 셀이 `75%`로 보이지만 내부 숫자가 `0.75`이고 숫자 서식이 퍼센트인 경우 자동으로 `75`로 변환합니다. 결과가 예상과 다르면 **Convert Excel percentage-formatted cells** 체크를 해제하고 다시 정리합니다.
6. 실측 기록임을 확인한 후 동의 체크박스에 체크하고 **3. Save reviewed data**를 누릅니다. 승인 후에만 사용자 프로필 폴더에 정규화된 JSON이 저장됩니다. 기존 AI 외부 데이터셋은 **덮어쓰기**되며 `actual_runs.csv` 또는 회사/개인 실험 DB에 자동 추가되지는 않습니다.
7. **ML target**에서 수득률(`actual_yield_percent`) 또는 순도(`actual_purity_percent`)를 선택한 뒤 **4. Train local AI**: 실측 데이터가 충분하면 로컬 머신러닝 모델을 학습합니다. 최소 **측정값 24행, 서로 다른 서열 6개 이상**, Scale/Loading 값의 유효성, 평가 모델의 기준 성능보다 좋은 결과 등을 검사합니다. 조건을 못 만족하면 모델 생성을 보류합니다.
8. Auto Plan에서 **Compare current peptide**를 눌러 유사 실험 3개와, 검증 조건을 만족하는 경우에만 탐색적 예측값을 확인합니다. **Attach evidence**는 이 근거를 Auto Plan 검토 초안에 첨부할 뿐 시약/당량/시간을 자동 변경하지 않습니다. **Export Draft JSON**에 `ai_evidence` 필드가 포함됩니다.

## 지원하는 열 이름 예시

| 표준 필드 | 인식하는 예시 | 필수 여부 |
|---|---|---|
| `sequence` | `Sequence`, `Peptide Sequence`, `서열`, `시퀀스`, `펩타이드서열` | 필수 |
| `actual_yield_percent` | `Yield %`, `수득률(%)`, `실측수득률` | 학습 시 선택 |
| `actual_purity_percent` | `Purity %`, `HPLC 순도`, `순도(%)` | 학습 선택 대상 (GUI에서 수득률/순도 선택 가능) |
| `scale_mmol` | `Scale (mmol)`, `스케일` | 모델 학습 시 필요 |
| `loading_mmol_g` | `Loading (mmol/g)`, `로딩` | 모델 학습 시 필요 |
| `resin` | `Resin`, `레진` | 권장 |
| `chemistry` | `Coupling system`, `커플링`, `커플링시약` | 권장 |
| `run_id` | `Run ID`, `실험번호`, `LOT` | 선택 |

원본 열을 정확히 매칭하지 못할 때는 드롭다운에서 매핑을 직접 바꿀 수 있습니다. `Actual yield`에는 **0–100% 실측 수득률**만 입력하십시오. `Yield (mg)` 또는 계산상 이론 수득량은 직접 같은 데이터로 사용하지 마십시오. 실험 기록과 실제 결과를 혼동하면 잘못 학습됩니다.

## ML 모델과 안전 제한

- `RandomForestRegressor` 및 `scikit-learn`을 사용합니다. **서열별 GroupShuffleSplit 홀드아웃 검증**을 사용해 같은 서열의 반복 실험이 학습·시험에 동시에 들어가지 않도록 합니다.
- 수득률 예측은 `sequence_length`, `Cys/Asp/Pro/Gly 수`, `Scale`, `Loading`, `Resin`, `Coupling system`만 사용합니다. 실제 수득률·순도·실험 이후 결과를 입력 특징으로 사용하지 않습니다.
- 단순한 중앙값 기준 예측보다 검증 MAE가 낮지 않으면 모델 배포를 거절합니다. 모델이 생성되어도 홀드아웃은 한 번의 검증일 뿐 독립적인 실험 검증/보증이 아닙니다.
- 입력 서열 길이, Scale, Loading, Resin 또는 Coupling System이 학습 데이터 범위를 벗어나면 추정값을 표시하지 않고 OOD 상태로 처리합니다.
- **Auto Plan 계산/시약량/보호기/반응 조건은 AI 때문에 자동으로 변경되지 않습니다.** 실제 실험 적용 전에 SOP·SDS·논문·작업자 검토가 필요합니다.
- 데이터와 로컬 모델은 설치 소스 폴더가 아닌 각 Public·Private 사용자 프로필 아래 `ai_excel_v9`에 분리 저장됩니다. **파일은 외부 서버로 전송되지 않습니다.** 작업자가 공개용 소스 패키지에 사내 실험 데이터를 수동 복사하는 행위까지 방지하지는 못합니다.
- 파일 포맷 제한: CSV/TSV와 `.xlsx`만 실질 지원. 오래된 `.xls`/암호화 Excel/복잡한 다중 헤더 표/장치 로그는 사용자가 변환하거나 매핑을 검토해야 합니다.
- 로컬 `.joblib` 모델 파일은 직렬화 코드 실행 위험 때문에 외부에서 내려받은 파일을 배치·가져오지 마십시오. 앱이 생성한 파일의 체크섬 일치를 검사한 후에만 불러옵니다.

## 테스트

- `PYTHONPATH=.:apps/spps_planner_app python -m pytest -q tests/test_v9_ai_excel_import.py`
- Linux GUI는 Xvfb에서 실행 가능한 경우만 검사하며, 실제 Windows EXE/Installer 및 Windows 네이티브 GUI 수동 시험은 별도입니다.

**버전 고정: SPPS Planner V9.0.0.** 실험적으로 승인된 수율/성공 확률/반응법 최적화 프로그램이 아닙니다.


**2026-11-08 개선:** 동일 서열의 다양한 표기를 합쳐 그룹 단위 검증을 3회 실시하고, 보호형/Cyclic 제품은 토폴로지 정보가 없는 ML 수득률 예측을 보류합니다. 자세한 내용: [AI 정밀 개선 내역](V9_AI_REFACTOR_HARDENING_KO.md).
