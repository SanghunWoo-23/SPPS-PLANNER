# SPPS Planner V9.0.0 — AI/ML Evidence & Safety Evolution

**개발본 · 2026-11-09 · 로컬 AI·ML 지원 · 실험적 검증 미완료**

## 핵심 변화

이번 변경은 기존 V9.0.0의 `Auto Plan → AI · Import Excel / CSV...` 경로를 확대하며, 기존 화학 엔진이나 Generate/Apply의 합성 조건 계산을 자동 수정하지 않는다.

1. **로컬 AI 모델을 데이터 전용 JSON으로 저장:** Excel AI의 RandomForest 학습 결과는 `ai_excel_yield_v9.forest.json` 또는 `ai_excel_purity_v9.forest.json`으로 저장한다. `joblib.load()`를 통해 Excel AI 모델을 실행하지 않는다. 모델 구조·각 트리의 노드·수치 유효성·파일 SHA-256을 검사하고 순수 Python으로 추론한다. 기존 `.joblib` 모델은 **재학습**해야 한다. *이 변경은 Excel AI에만 적용되며, 과거 별도 ML Lab의 저장 형식까지 일괄 교체한 것은 아니다.*
2. **학습 준비도 진단:** `Audit data quality`에서 중복 Run ID, 반복 행, 서열 파싱, 실측값 부족, Scale·Loading 결측, 서열 다양성 부족을 확인하고 목표별로 학습 가능한지 설명한다. 실제 모델 성능이 좋다는 뜻은 아니다.
3. **데이터 오입력 방지:** 빈 `.xlsx` 템플릿 생성 버튼 추가. `Runs` 시트에는 **헤더만** 포함되고 실제 실험·수득률·시약값을 지어내지 않는다. `GUIDE` 시트에서 입력 단위와 제품 형태를 설명한다.
4. **보호형·Cyclic 데이터 분리:** Excel에서 `Product path` 및 `Reaction step`을 매핑할 수 있다. 현재 로컬 RandomForest 수득률/순도 모델은 `linear_deprotected` 및 과거 비표기 Linear 데이터만 학습한다. 명시된 Cyclic·Branched·Protected 데이터는 별도 실제 실험 기록으로 보존하되 현 모델 학습에서 제외한다. 보호기/분지 표기가 있는 서열도 기본 1차원 모델의 예측을 보류한다.
5. **그룹 단위 검증 3회 유지 + 설명 개선:** 같은 펩타이드 서열을 학습·검증 양쪽에 넣지 않는 GroupShuffleSplit 평가와 중앙값 기준 비교를 유지한다. 검증 데이터의 절대 오차 분위수(80%·90%)를 저장하고 예측 시 **참고 오차 구간**을 표시한다. 이 값은 통계적으로 보장된 신뢰구간이나 정식 Conformal Prediction 구간이 아니다. 반복 그룹 분할 사이에는 같은 그룹이 등장할 수 있기 때문이다.
6. **홀드아웃 특징량 중요도:** 첫 번째 홀드아웃에서 Permutation Importance를 계산해 최대 5개 특징량과 MAE 변화(percentage points)를 저장한다. 이는 모델이 참조한 통계적 관계이지 화학적 인과관계·최적 조건의 증거가 아니다.
7. **Out-of-distribution 검토 확대:** 기존 서열 길이·Scale·Loading·Resin·Coupling 시스템·D/비천연/Branch count 범위뿐 아니라 학습에 존재하지 않았던 잔기 identity가 있으면 예측을 보류한다.

## 실제 사용법

1. `Auto Plan (Optional)`에서 AI/Excel Assistant를 열고 `Create blank Excel template`로 입력 서식을 생성하거나 실제 CSV/XLSX를 바로 선택한다.
2. Excel/CSV를 선택해 컬럼을 자동 매핑한 뒤 원자료와 비교하고 `Check & clean`을 수행한다. 파일이 여러 개라면 **각 파일을 따로 검토·Stage**한다.
3. `Audit data quality`에서 데이터 품질·학습 준비도를 확인한다. 실험 기록의 진위와 조건·제품 유형을 점검한다.
4. 승인 후 Append/Replace 모드로 저장한다. 수득률 또는 순도를 선택하고 별도 클릭으로 학습한다.
5. 현재 펩타이드와 비교한다. 학습 데이터 범위 내에서 신뢰성 검사를 통과한 경우에만 **탐색적 추정치**를 표시하며 `Attach evidence`는 검토용 정보만 연결한다. **반응 조건과 Checklist를 자동 변경하지 않는다.**

## 데이터 주의

- 수득률(%)은 분리 수득률 등 실제 측정 정의가 다른 자료를 섞으면 안 된다. Purity, Crude Yield, Purification Recovery, Cyclization conversion은 별도 지표다.
- `Product path` 지원값: `linear_deprotected`, `linear_protected`, `cyclic_protected`, `cyclic_deprotected`, `branched_deprotected`, `branched_protected`.
- 보호형·분지·Cyclic 데이터를 선형 모델에 강제로 입력하지 않는다. 이 항목들의 독립 예측은 각 반응의 보호기·결합 위치·반응 Method·정제 결과가 데이터에 명확히 기록되고 별도 검증된 후 개발한다.
- 데이터는 로컬 Public/Private 프로필에 분리 저장한다. Public ZIP에는 사내 관측 데이터, Private 시드, 학습된 로컬 모델을 포함해서는 안 된다.
- `RandomForestRegressor`는 생성형 LLM이 아니다. ChatGPT API·클라우드 연동도 없다.
- Windows 네이티브 GUI/EXE/Installer 실사용 및 wet-lab 수득률 예측 성능은 검증되지 않았다.

## 이론과 공식 출처

- scikit-learn, *Common pitfalls and recommended practices*: https://scikit-learn.org/stable/common_pitfalls.html
- scikit-learn, *Permutation feature importance*: https://scikit-learn.org/stable/modules/permutation_importance.html
- scikit-learn, *Model persistence*: https://scikit-learn.org/stable/model_persistence.html
- MAPIE, *Conformal Prediction*: https://mapie.readthedocs.io/en/latest/

**정확한 구분:** 이 개발본의 “참고 오차 범위”는 MAPIE가 제공하는 분할 Conformal Prediction의 이론적 커버리지 보장과 다르다. 정식 Conformal 적용은 독립적인 calibration data와 적용 가정 검증 이후에만 가능하다.

## 변경 파일 및 후속 개발

- `suite_gui/ai_safe_forest_v9.py` 신규: 안전한 순수 데이터 모델 저장·검증·추론
- `suite_gui/ai_excel_core_v9.py` 수정: 데이터 유형 구분, 학습 준비도, 홀드아웃 설명, OOD 검사, 템플릿
- `suite_gui/ai_excel_dialog_v9.py` 수정: 템플릿 생성 버튼, 진단 보고서 표시
- `tests/test_v9_ai_ml_evolution_safe_model.py` 신규: 추론 동등성, 손상 데이터 거부, 보호형 보류, 보고서와 템플릿
- 기존 `test_v9_ai_excel_import.py`, `test_v9_ai_excel_refactor_guards.py`, `test_v9_reaction_ai_guards.py`: 구형 모델 형식 또는 잘못된 제품 유형 기대값 갱신

**후속 과제:** 반응 단계 및 제품 유형별 독립 모델; Purification Recovery·Cyclization Conversion 분리; 실제 외부 배치 검증; 그룹 독립 calibration을 갖춘 Conformal interval; 해석 가능한 화학적 feature set 확장; Windows 네이티브 설치·동작 검사.
