# SPPS Planner V9.0.0 — 분자 구조·이론 MS·외부 ML 검증 고도화 (2026-11-11)

이 문서는 **실제로 구현된 소스 기능**과 **실험적·운영적 미검증 사항**을 분리해 설명합니다. 버전은 V9.0.0을 유지합니다. 합성 성공, 분자 동일성의 실측 확인, GMP 적합성 또는 최적 SOP를 의미하지 않습니다.

## 이번 개선

1. **Head-to-tail 말단 식별 정확화:** RDKit 구조의 residue/atom identity로 주쇄 N-terminal N과 C-terminal OXT를 구별합니다. Lys 측쇄 NZ 때문에 `SKS`, `S(tBu)KS(tBu)` 고리화 검산이 차단되던 문제를 해결했습니다. 자유 Pro N-terminal (2차 아민)도 지원합니다. N-terminal Ac/Boc 및 C-terminal amide는 여전히 차단합니다.
2. **명시적 Branch + Cyclic 검산:** `lysine_branch_head_to_tail` 토폴로지를 신설했습니다. 예를 들어 `AK(GGEP)S`, `AK(Dde)(GGEP)S`의 단일 Lys ε-amide 분지에 대해 **주쇄 자체**가 N-to-C 고리화되는 구조만 검산합니다. 분지 아민의 고리화, 다중 분지, 분지의 D형·비천연 AA, 다중 고리 및 다른 링크는 지원하지 않습니다. Dde/ivDde/Mtt는 분지 결합 이전 제거된 *합성 핸들*로만 취급하며, 제거 실제 성공 여부는 모릅니다. 반응법·시약량은 자동 생성하지 않습니다.
3. **LC-MS 검토용 `m/z` 후보:** 통과한 RDKit 분자식의 중성 **monoisotopic mass**로 [M+H]+, [M+2H]2+, [M+3H]3+, [M+Na]+, [M+K]+, [M−H]−를 계산합니다. 평균 MW와 모노아이소토픽 질량을 혼동하지 마세요. 전하·부가 이온의 형성, 동위원소 패턴, 기기 보정, 실측 피크 존재 여부는 예측하지 않습니다. Checklist에는 재검증된 구조의 [M+H]+ 후보를 'theoretical / not observed'로 기록합니다.
4. **독립 ML 평가 보호:** 학습 파일과 외부 파일의 정규화된 서열뿐 아니라 Run ID 중복도 평가 전에 차단합니다. 성공적으로 예측된 **서로 다른 서열 그룹** 개수가 기준 미만이면 외부 검증 평가 상태를 보류합니다. 반복 측정이 많은 서열의 영향력을 줄인 서열 균형 MAE, 짝수 개 관측값의 올바른 Median Absolute Error, 조건부 예측구간의 *경험적 행 단위* 포함률을 기록합니다. 포함률은 보장된 신뢰구간이 아닙니다.
5. **재현 가능한 화학 계약 검사:** `python tools/validate_v9_chemistry_matrix.py`는 주요 지원/거부 사례를 검사하며, 옵션 `--out`으로 원자료 없이 JSON 보고서를 생성합니다. 새 Windows CI에는 실제 `PyInstaller` EXE 빌드와 해당 EXE `--self-test`를 수행하는 명령을 추가했습니다. 이 CI가 실제 성공했다는 뜻은 아닙니다.

## 사용

`Auto Plan (Optional)` → `Independent molecular graph / Cross-link...`에서 `Main-chain head-to-tail + Lys branch`를 선택합니다. Branch는 주쇄 Lys 잔기에 명시된 **단일** L형 펩타이드 분지만 지원합니다. 구조 그래프가 `CROSSCHECK_PASS`를 반환하더라도 반응 Method는 여전히 승인되지 않은 검토 자료입니다. 생성된 JSON의 `theoretical_ms_ions` 값과 Checklist의 'NOT an observed analytical peak' 고지를 확인하세요.

외부 ML 데이터 평가:

```bat
python tools\external_ml_validation_v9.py --train-dir "C:\Train" --model-dir "C:\Models" --external "C:\Independent\test.xlsx" --target cyclization_yield_percent --out "C:\Reports\holdout.json"
```

기존 훈련 데이터와 다른 시퀀스라는 조건만으로 외부 데이터 독립성이 증명되지는 않습니다. 실제 독립 실험/LOT/날짜 기록을 확인해야 합니다. 결과 JSON에는 시퀀스·Run ID를 출력하지 않습니다.

## 아직 해결·검증이 필요한 부분

- **실험적 미검증:** 실제 펩타이드의 결합 구조 확인, Cyclization 수율·부산물·순도, 독립 실험 수득률 모델 예측 정확도. 이를 완료하려면 HPLC/MS, SOP, 외부 실험 데이터가 필요합니다.
- **미지원 화학:** 임의 비천연 아미노산의 구조, Pbf 등 일부 보호기, 복합 다중 분지 및 분지/측쇄 이중 고리, CuAAC·Thioether·RCM 등의 반응 적용과 단계별 중간체 원자 그래프.
- **Windows:** 실제 Windows PC에서의 PyInstaller EXE/Installer 설치·제거·업그레이드 및 장시간 UI 시험. CI 명령을 구성했지만 실제 해당 워크플로우 실행 결과는 현재 확인되지 않았습니다.
- **논문 AI:** Crossref 서지 메타데이터 검색은 지원하지만, 저작권·접근권한이 없는 전문을 자동 수집/학습하거나 생성형 AI로 검증된 SOP를 제공하지 않습니다.

다음 개발에서 새 화학 반응을 지원할 때는 반응 원자 지도/보호기 구조/정확 분자식 → 독립 MW·m/z 계산 → 실측 분석 검토 → 반응조건 적용 승인 순서로 검증해야 합니다. 알 수 없는 입력은 `WITHHELD`로 처리하며 기본 SPPS 엔진에 추정값을 주입하지 않습니다.
