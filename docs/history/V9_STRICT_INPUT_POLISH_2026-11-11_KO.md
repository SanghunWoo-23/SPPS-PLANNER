# SPPS Planner V9.0.0 — 엄격한 화학·AI 입력 검증 (2026-11-11)

## 이번 코드 변경

- **Monomer atom mapping:** Custom amino acid/보호형 아미노산의 정확한 atom-mapped SMILES가 없으면 질량을 계산하지 않습니다. 등록된 `token`과 별도로 제공된 `smiles`가 실제 구조·입체화학·원자 맵에서 다를 경우 계산을 거부합니다.
- **공급업체 MW 검사:** Monomer 표에서 `reported_mw`(또는 `mw`) 열에 **단일 중성 분자의 평균 MW (g/mol)**를 넣으면 RDKit 구조 계산과 교차 검증합니다. 차이가 0.25 g/mol을 넘으면 해당 행을 거부합니다. Salt/counterion/solvate가 포함된 공급업체 MW는 그대로 비교하면 안 되며, 별도 조성 확인이 필요합니다. 빈 칸은 자동으로 만든 실측 근거가 아닙니다.
- **JSON 계약:** 중복 JSON 속성, NaN/Infinity, 200 kB 이상의 구조 입력을 거부합니다. `head_to_tail` 등이 파일에서 중복돼 마지막 값이 조용히 선택되는 문제를 방지합니다. GUI 직접 입력·파일 입력·Catalog JSON에 동일 정책을 적용합니다.
- **CSV/Excel:** `token`, `smiles` 헤더는 고유해야 하고, 초과·중복·비정상 자료는 검토 없이 적용하지 않습니다.
- **원자 구조 단계별 질량:** Custom Molecular Graph의 중간 조립 단계마다 중성 평균 MW, 정확질량, 분자식, 연결 성분 수를 저장합니다. 레진 결합 상태의 측정 질량이나 실제 반응 진행률이 아닙니다.
- **선택형 논문 AI:** 응답의 중복 출처 ID와 인용 없는 결론을 거부합니다. 원문에 있는 직접 인용이 확인되어야 분석용 초안으로 표시합니다. 이는 반응 조건의 과학적 타당성 검증과 다릅니다.
- **무GUI 검증 명령:** `python tools/review_custom_topology_v9.py topology.json --catalog monomers.xlsx`에서 화학 구조를 읽고 전체 결과를 JSON으로 출력합니다. 계산 성공만 종료 코드 0, 그 외 종료 코드 2이며 임의의 합성 조건은 생성하지 않습니다.

## Catalog 예시 (CSV)

```csv
token,smiles,reported_mw,source
Aib,[NH2:1]C(C)(C)[C:2](=O)[OH:3],103.12,사용자 확인 자료
```

**주의:** 위 질량값은 예시로 작성한 입력이므로 반드시 직접 계산·검토해야 하며, 시약병의 Fmoc/Boc 보호기·염·수화물 등을 포함한 시약 질량이 아닙니다. `reported_mw` 미입력 시 구조 기반 MW만 계산합니다.

## 검증 경계

- 구조가 계산되는 것과 고리화 선택성·반응 성공률·합성 조건이 실험적으로 검증되는 것은 다릅니다.
- 이번 입력 검증은 기존 SPPS 계산 엔진의 반응 당량을 변경하지 않습니다.
- 외부 실제 실험 데이터 기반 수득률 모델 정확도, Windows 실제 설치·업그레이드·제거·장기 GUI 안정성은 별도 시험 없이는 PASS로 기록하지 않습니다.
- Public ZIP에는 Private 시드·DB·실험 모델을 포함하지 않습니다. GitHub에는 Public만 공개합니다.
