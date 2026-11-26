# SPPS Planner V9.0.0 — Extended Graph / External ML / Literature (2026-11-10)

이 문서는 **개발 완료(소스)**와 **미검증(실험 또는 운영 환경)**을 구분합니다. 이 기능은 실험 SOP가 아닙니다.

## 1. 기존의 안전한 계산 흐름은 유지

- Project Manager, Step 1/2, Generate/Apply, Materials, Checklist, Workup 및 `engine.py`는 유지됩니다.
- 추가 기능은 독립적으로 검증된 **분자 연결 그래프**와 **참고 검토 화면**입니다. 기존 시약량 계산 및 실험 계획을 자동 변경하지 않습니다.
- 버전은 계속 **V9.0.0**입니다. Private 데이터·로컬 모델은 Public ZIP에 넣으면 안 됩니다.

## 2. 분자 그래프 교차검증

Auto Plan (Optional) → **Independent molecular graph / Cross-link...**를 누릅니다.

| 입력 타입 | 현재 지원 | 질량 변화/주의 |
|---|---|---|
| 자연 L/D amino acid | 혼합된 표준 20종, 명시적 D형 | alpha stereochemistry 보존, Gly는 무키랄 |
| 보호형 제품 | S/T/Y(tBu), D/E(OtBu), K(Boc), C(Acm/StBu/Trt) | 명시된 결합 원자에 보호기 구조를 붙여 MW·분자식 계산 |
| Head-to-tail | 자유 Nα와 자유 C-terminal COOH | 물 한 분자 축합; 보호형 잔기 유지 가능 |
| Lys branch | `K(GGEP)` 등 자연 L형 분지, 자유 말단 | Lys ε-NH2와 분지 C-terminal의 amide 결합 |
| Disulfide | 두 Cys 위치를 각각 **1-based** 입력 | Cys thiol이 자유 상태여야 하며 총 H2 손실 |
| Side-chain lactam | Lys와 Asp 또는 Glu 위치를 각각 **1-based** 입력 | 유리 ε-NH2와 측쇄 COOH 필요, 물 한 분자 축합 |

모델이 지원하지 않는 `Pbf`, `Dde`, `ivDde`, `Mtt` 또는 비천연 아미노산/다중 분지/모호한 구조는 **WITHHELD**로 기록합니다. `Trt`는 Cys(S-Trt)에만 구조적으로 구현했으며 다른 residue의 regioisomer를 추측하지 않습니다. 일반적인 분자 그래프를 만든다고 고리화의 반응성, 수율, 3D 구조, 부반응 또는 보호기 탈보호 실험 성공이 증명되지는 않습니다.

현재의 `mass_balance_v9` 기반 보호기 델타 값은 평균 질량(반올림 포함)입니다. **StBu는 88.17 g/mol로 수정**했습니다. Fmoc-Cys(StBu)-OH의 알려진 구조 C22H25NO4S2 및 분자량 약 431.58과 비교했습니다. 기존 프로젝트에서 Cys(StBu)가 포함된다면 이전에 저장한 이론 MW를 **재계산**하세요. 출처: Bachem Fmoc-Cys(StBu)-OH (https://shop.bachem.com/product/4007445/), RSC cysteine protecting groups review https://pubs.rsc.org/en/content/articlehtml/2021/cs/d1cs00271f.

## 3. 외부 ML 실측 데이터 독립 검증

훈련에 사용하지 않은 **독립 실험 파일**을 확보한 경우 아래처럼 읽기 전용 평가를 수행합니다. 단순한 외부 파일 존재만으로 자동 검증 완료가 되는 것이 아닙니다.

```bat
python tools\external_ml_validation_v9.py --train-dir "C:\TrainingReviewed" --model-dir "C:\LocalModels" --external "C:\Independent\external_runs.xlsx" --target cyclization_yield_percent --out "C:\Reports\external_evaluation.json"
```

평가 전 **정규화된 서열 집합과 겹치는 기록이 있으면 전체 평가를 거부**합니다. 데이터가 적거나 학습 범위를 벗어나면 성능을 확정하지 않습니다. MAE 및 편향은 실측 대조값이 충분한 경우만 집계합니다. 모델 학습, 데이터 편집, 결과 승인 승격은 수행하지 않으며 출력에는 서열·Run ID를 저장하지 않습니다.

## 4. 연구 근거 검색

Auto Plan의 오프라인 근거 목록은 유지합니다. **Search Crossref online (opt-in)**는 사용자에게 외부 전송을 확인받은 경우에만 검색창의 **수동으로 입력한 일반 키워드**를 Crossref에 전송합니다. 프로젝트 서열·실험 기록은 자동 전송하지 않습니다. 조회는 GUI 작업 스레드에서 실행하며 조회 실패 시 경고만 표시합니다.

결과는 DOI와 제목 등 **서지정보**일 뿐, 전문 읽기·문헌 실험법 추출·생성형 AI 최적화가 아닙니다. 외부 논문 메타데이터를 SOP나 합성 조건으로 자동 적용하지 않습니다.

## 5. 검증 및 제한

- Python `python main_launcher.py --self-test`, `pytest`, `tools/verify_windows_release.py`는 소스 수준 검사입니다.
- Windows CI 워크플로우에 RDKit 설치 및 `tools/windows_acceptance_v9.py`를 추가했지만, **CI가 실제로 실행된 결과나 Installer 설치·제거가 검증되었다는 뜻은 아닙니다**.
- 실제 실험 수율·순도 외부 검증은 사용자의 분리된 측정 데이터가 있어야 가능합니다.
- 복잡한 변형 AA/다중 고리화/Click/Thioether/유도체의 원자 그래프는 미지원이며, 근거 없는 계산을 대신하지 않습니다.
