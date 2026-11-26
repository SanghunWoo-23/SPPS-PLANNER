> **최신 개발 업데이트:** 단일 Lys ε-amide Branch `K(GGEP)`의 전체 제품 MW는 이제 제한적으로 지원합니다. 단계별 Branch Checklist MW 및 다른 고리화 기전은 미지원입니다. [최신 반응/Branch 가이드](V9_REACTION_AND_BRANCH_KO.md)를 우선 확인하세요.

# SPPS Planner V9.0.0 — 보호형 펩타이드 MW·Checklist·수득량 시나리오

> V9.0.0 **개발 빌드**의 신규 기능 설명. 현재 Windows EXE/Installer 및 실제 실험 성능은 검증하지 않았다.

## 1. 입력할 수 있는 표기

- **Fmoc 없는 측쇄 보호형 아미노산 단독 입력:** `H-Ser(tBu)-OH`, `H-Arg(Pbf)-OH`, `H-Glu(OtBu)-OH`, `H-Lys(Boc)-OH`, `H-Cys(Trt)-OH` 등. Bundled `compounds.csv`에 31개 Nα-Fmoc-free protected AA 항목을 추가했다.
- **서열 안에서 해당 완제품을 사용:** `[H-Ser(tBu)-OH]-G` 같이 대괄호 표기로 명시한다. 주쇄 일반 입력은 `S(tBu)-V-S(tBu)` 등 원래 표기를 사용할 수 있다.
- **정확한 보호기 구별:** `K(Dde)`와 `K(ivDde)`는 서로 다른 화학종이며 같은 MW/조건으로 취급하지 않는다.
- **N-아세틸 보호형 마지막 아미노산:** `Ac-Ser(tBu)-OH-G` 등 기존 Ac-AA 토큰을 일부 MW 계산에 반영. 실제 합성 계획 지원 범위는 별도로 점검한다.
- 보호형 전구체 Reagent MW는 일반 `Product MW contribution`과 다르다. 단량체 원료 MW와 합성된 펩타이드 MW를 같은 열로 사용하지 않는다.

## 2. Auto Plan 경로

Project Manager → Auto Plan (Optional) → **Final product** 선택:

1. Linear — fully deprotected
2. Linear — side-chain protected (selective cleavage)
3. Head-to-tail — cyclic, still protected
4. Head-to-tail — cyclic, globally deprotected

**Side-chain groups** 선택: `Catalog precursor`(기본; 기존 Fmoc-AA 전구체의 측쇄 보호기 *유지 가정*), `Only explicitly annotated groups`, `None`.

Generate Full Plan을 선택하면 이전 Plan을 만드는 기존 엔진을 호출한다. 별도로 Checklist에 `peptide_mw`와 `mw_form`을 추가한다. 보호형·Cyclic 경로를 명시한 경우에만 **반응 검토용** Selective Cleavage / Head-to-tail / Global Deprotection 행을 덧붙인다. 이 행은 시간·시약 시스템·성공 여부를 자동 확정하는 SOP가 아니다.

## 3. 보호형 선택적 Cleavage와 Head-to-tail MW

- 중간체 MW: 펩타이드의 **자유 분자 등가 평균 중성 MW**. 레진 무게/링커는 미포함. Wash에서 원칙적으로 변화하지 않고 Coupling 및 Fmoc 제거로 변한다.
- 선택적 Cleavage 후 Linear/Protected: **측쇄 보호기 질량이 유지되었다는 가정**으로 계산. 실제 TFA 감도, Trt 탈락 가능성, Side-chain deprotection은 별도로 검증한다.
- Head-to-tail cyclization: 자유 N-terminal amine과 자유 C-terminal COOH가 유효할 때, `protected linear MW − H₂O (18.01528 g/mol)`로 계산.
- 최종 전역 탈보호: 모든 잔기별 보호기의 계산상 증가 질량을 제거한 cyclic/linear MW. 실제 탈보호 완결 여부는 LC-MS/HPLC 등으로 확인한다.
- `Rink Amide`처럼 amide 말단, `Ac-` 같은 N-terminal cap, 단량체에는 자동 head-to-tail cyclization MW를 제공하지 않는다. **분지, 다른 ring topology, 알 수 없는 토큰**에는 거짓 MW 대신 미지원 경고를 낸다.
- **특히 Trt 보호기는 약산성 Cleavage에서도 일부 손실될 수 있다.** 보호형 경로의 질량은 지정한 보호기가 실제 남는다는 *조건부 계산값*이다.
- C-terminal starter가 외부에서 이미 레진에 결합된 2-CTC 경로에서 Plan에 그 잔기가 생략되면, Checklist MW는 해당 잔기가 **존재한다고 가정하고** 계산하며 별도 주의를 표시한다.
- 표의 MW는 **평균 질량/중성 분자량**이다. MALDI 등에서 쓰는 단일동위원소 [M+H]⁺ 값과 같지 않다. 염, 용매화물, Counterion, 산화 부산물, 불완전 탈보호는 추가하지 않는다.

## 4. MW 계산 예시 (이론값; 기본 소수 자릿수는 카탈로그 반올림에 따름)

`dS-dV-dS` · 2-CTC · 카탈로그의 dSer(tBu) 두 잔기 보존 가정:

| 상태 | 평균 중성 MW (g/mol) |
|---|---:|
| Linear, 완전 탈보호 | 291.305 |
| Linear, 측쇄 tBu×2 보존 (= selective cleavage 후 가정) | 403.525 |
| Head-to-tail cyclic, tBu×2 보존 | 385.510 |
| Head-to-tail cyclic, 완전 탈보호 | 273.290 |

비교: `H-Ser(tBu)-OH` 원료 평균 MW ≈ **161.20 g/mol**(보호기 없는 H-Ser-OH ≈ 105.09 g/mol). 위 숫자는 수율이나 반응 가능성을 보증하지 않는다.

## 5. 수득률 추정은 실험 예측이 아니라 사용자가 입력한 시나리오

기본 출력은 `Theoretical mass (g) = MW (g/mol) × Scale (mmol) × Copies ÷ 1000`이다.

다음 값은 **직접 입력해야만** 추정량을 계산한다.

- Coupling conversion (%) — 이상화된 *단계당* 평균 전환율
- Cyclization recovery (%) — cyclic 경로 선택 시 필수 입력
- Isolation recovery (%) — Cleavage/Workup/정제/침전 등 실제 회수율을 사용자 가정으로 한 번에 표현

예시 모델: `Mass_scenario = Mass_theoretical × (Coupling_fraction ^ assumed_coupling_steps) × Cyclization_fraction_if_any × Isolation_fraction`.

**가정하지 않는 것:** 자동 ML 수율, 예상 순도, 반응 선택성, Resin 실제 Loading 편차, 원료 손실/부반응, 단계별 측정값 없는 최적화. `coupling_steps`는 일단 `residue_count − 1` 단순 계산으로 기록하며, 실제 사용 단계(특히 preloaded resin, branch, special coupling)와 다를 수 있어 검토가 필수다.

프로젝트에는 `v9_mass_options`, `v9_yield_scenario`가 각각 저장된다. JSON Draft에는 질량 상태, 보호기 가정, 수득량 계산 상태, 사용자가 입력한 백분율이 남는다. 승인은 기존 엔진으로 계획을 생성했다는 의미일 뿐 실험적 검증은 아니다.

## 6. 보호기·결합 근거

- Fmoc-protected amino acids and free-Nα MW: https://www.tpims.org/info/calculator/mw_calculator
- Peptide cyclization, side-chain protected linear precursor: https://pmc.ncbi.nlm.nih.gov/articles/PMC7314982/
- CTC mild selective cleavage with side-chain protection: https://pubmed.ncbi.nlm.nih.gov/1917309/
- Fmoc-Lys(Dde)-OH reference: https://pubchem.ncbi.nlm.nih.gov/compound/Fmoc-Lys_Dde_-OH
- Fmoc-Lys(ivDde)-OH reference: https://www.tcichemicals.com/KR/ko/p/F1321

이 기준 자료는 일반적인 반응/구조의 근거이며 **실제 사용 원료의 lot별 공급사 CoA/SDS, 분자식, 화학형(염·용매화물), 분석 데이터** 확인을 대체하지 않는다.
