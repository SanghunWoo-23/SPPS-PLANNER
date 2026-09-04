<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="160">

# SPPS Planner V5.0.0

**고체상 펩타이드 합성(SPPS)의 계획·계산·기록·근거 기반 추천을 하나로 연결하는 Windows 우선 데스크톱 소프트웨어**

Sequence parsing · 편집 가능한 합성 Plan · Materials · Checklist · Batch · Cleavage · 실험 이력 · Evidence-driven Recommendation

[![Release](https://img.shields.io/badge/release-V5.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)
[![License](https://img.shields.io/badge/license-Custom%20Academic%20Citation-6B7280?style=for-the-badge)](LICENSE)

**[English README](README.md) · [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md) · [English User Manual](docs/USER_MANUAL_EN.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)**

Repository: **SanghunWoo-23/SPPS-PLANNER**

</div>

---

## 목차

- [SPPS Planner가 무엇인가](#spps-planner가-무엇인가)
- [릴리스 상태](#릴리스-상태)
- [핵심 설계 원칙](#핵심-설계-원칙)
- [V5.0.0의 핵심 변화](#v500의-핵심-변화)
- [기능 요약](#기능-요약)
- [전체 작업 흐름](#전체-작업-흐름)
- [빠른 시작](#빠른-시작)
- [Sequence 입력과 Parser](#sequence-입력과-parser)
- [Plan 생성과 Apply Change](#plan-생성과-apply-change)
- [Materials · Checklist · Batch](#materials--checklist--batch)
- [Loading Advisor](#loading-advisor)
- [Cleavage Advisor](#cleavage-advisor)
- [Post-cleavage NH4I Rescue](#post-cleavage-nh4i-rescue)
- [Recommendations & Lab History](#recommendations--lab-history)
- [Natural-language Issue Log](#natural-language-issue-log)
- [Run 추적성](#run-추적성)
- [Evidence / ML 정책](#evidence--ml-정책)
- [Public 데이터 정책](#public-데이터-정책)
- [Runtime 데이터](#runtime-데이터)
- [저장소 구조](#저장소-구조)
- [Windows 빌드](#windows-빌드)
- [검증과 회귀 테스트](#검증과-회귀-테스트)
- [성능 설계](#성능-설계)
- [과학적 범위와 한계](#과학적-범위와-한계)
- [문서 안내](#문서-안내)
- [기여](#기여)
- [인용](#인용)
- [라이선스](#라이선스)
- [문제 해결](#문제-해결)
- [FAQ](#faq)

---

## SPPS Planner가 무엇인가

SPPS Planner는 **고체상 펩타이드 합성(SPPS)의 실제 작업 흐름을 계획하고 추적하기 위한 데스크톱 프로그램**이다.

단순히 sequence를 넣고 숫자만 계산하는 프로그램이 아니라 다음을 하나의 흐름으로 연결한다.

```text
Project / Peptide 정의
        ↓
Sequence + modifier + resin + scale + loading + chemistry
        ↓
Generate
        ↓
편집 가능한 Plan
  ├─ Materials
  ├─ Checklist
  ├─ Total Materials
  ├─ Cleavage
  └─ Export / Batch
        ↓
실제 실험 수행
        ↓
측정 Result 또는 자유문장 Issue 입력
        ↓
현재 Planner 조건 + active Run 자동 연결
        ↓
Verified 실험 근거 축적
        ↓
다음 추천의 근거가 점점 좋아짐
```

V5에서 가장 중요한 방향은 **“화면을 더 많이 만드는 것”이 아니라 “Planner가 이미 아는 정보를 다시 입력시키지 않고, 실제 결과를 근거로 다음 판단을 더 잘하게 만드는 것”**이다.

---

## 릴리스 상태

**V5.0.0은 현재 Public GitHub 릴리스이다.**

Public 버전은 내부/개인 실험 이력을 번들하지 않는다. 실험 DB가 비어 있는 상태에서도 기존 SPPS Planner의 계획·계산 기능과 public-safe fallback이 동작하며, 사용자가 자신의 권한 있는 데이터를 로컬에서 기록하거나 import하면서 evidence system을 구축하는 구조다.

V5는 기존 검증된 Generate / Apply Change 계산 경로를 없애거나 대체하지 않는다. 그 위에 실험 결과 기록, Run 연결, 근거 표시, Loading/Cleavage 추천, model registry, natural-language issue 기록 등을 추가했다.

최종 Public 소스 패키지는 **273 passed / 22 skipped**, release verifier PASS, Windows release contract PASS 상태로 검증했다. Public experimental seed에는 문서만 포함된다.


---

## 핵심 설계 원칙

### 1. 화면에 보이는 Plan이 실제 기준이다

`Generate` 후 사용자가 Plan을 직접 수정할 수 있다. 그 다음 `Apply Change`를 누르면 원래 sequence에서 몰래 다시 생성하지 않고 **현재 보이는 Plan을 기준으로** Materials, Checklist, Totals 등의 연결 결과를 다시 계산한다.

### 2. 계획값과 실험값은 다르다

Planner에 입력한 조건은 **Plan condition**이다. 실제 실험을 수행했다는 증거가 아니다.

실험 근거가 되려면 실제 Result / Issue / Outcome 등이 Run과 연결되어야 한다.

### 3. 보호기와 실제 reagent form을 함부로 합치지 않는다

Fmoc-AA의 보호기 형태, D-form, non-natural residue, branch handle, modifier, linker, label, tag는 화학적으로 의미가 다를 수 있으므로 가능한 한 bottle-level identity를 유지한다.

### 4. 근거 종류를 구분한다

다음은 같은 것이 아니다.

- 실제 측정된 historical evidence
- operator-approved rule
- empirical estimate
- model prediction
- 일반 chemistry / literature reference

프로그램은 이들을 가능한 한 구분해서 보여주는 방향으로 설계되어 있다.

### 5. Model은 자동으로 몰래 재학습하지 않는다

Result를 하나 입력했다고 모델이 즉시 바뀌지 않는다. Loading model rebuild는 명시적으로 실행하며, 후보 모델의 validation 성능을 기록하고 active model과 비교한다.

### 6. Public에는 private 실험 이력을 넣지 않는다

GitHub 공개판은 빈 experimental seed에서 시작한다. 사용자는 자신의 로컬 데이터로 evidence를 쌓는다.

### 7. 최종 판단은 operator가 한다

SPPS Planner는 계획/검토/추천 도구다. 승인된 SOP, SDS, 안전 규정, 장비 적격성, 분석법 검증, 숙련된 연구자의 판단을 대체하지 않는다.

---

## V5.0.0의 핵심 변화

- **Target Loading → Recommended AA eq** 형태의 Loading Advisor
- 동일 resin + 동일 loaded/C-terminal AA 기반의 **bounded interpolation**
- 관측 범위 밖 extrapolation을 근거 있는 값처럼 보여주지 않음
- Verified measured loading 데이터만 사용하는 명시적 Loading model rebuild
- model candidate / active model / rollback 관리
- Cys가 있는 경우 **100 eq × Cys 개수** cleavage hard rule
- non-Cys sequence용 public-safe empirical length baseline
- post-cleavage **NH4I Reduction** rescue workflow
- NH4I를 cleavage cocktail에 자동 삽입하지 않음
- Add Result / Add Issue 중심의 간단한 실험 기록 흐름
- 한국어 / 영어 / 혼합 문장을 처리하는 natural-language Issue parser
- Result / Issue / Cleavage / Outcome에 active Run과 Planner condition snapshot 연결
- Recommendations / Advanced(History, Risk & Evidence, Data Health) 구조
- Batch material grouping 개선
- Fmoc-Cit-OH를 Non-natural AA로 분류
- Recommendations / Lab History 창의 체감 오픈 속도 개선
- Public/Private 공통 기능 source parity 유지

---

## 기능 요약

| 영역 | 기능 |
| --- | --- |
| Sequence | natural AA, terminal group, D/non-natural AA, chemical, linker, label, tag, branch-capable unit 처리 |
| Resin / Loading | resin family, loading, scale, resin-dependent volume 및 loading workflow |
| Plan | 합성 step 생성, 직접 편집, Repeat / Doubling 등 적용 |
| Apply Change | 현재 Plan을 유지한 채 연결 결과 재계산 |
| Materials | resin, AA, reagent, additive, base, solvent, modifier 등 계산 |
| Checklist | 전체/축약 실행 checklist |
| Cleavage | cleavage eq, cocktail, 시간, amount, workup 분리 및 추천 |
| Project Manager | 여러 peptide work item 관리 |
| Batch Manager | 여러 peptide를 동시에 계산하고 total material 집계 |
| Custom DB | 사용자 정의 AA / chemical / reagent / solvent / resin 등 |
| Experimental Data | Loading, Cleavage, Sequence, Usage, Outcome, Issue 기록 |
| Recommendations | historical evidence + bounded recommendation + explicit model support |
| Risk & Evidence | sequence/stage 위험 및 유사 실험 근거 표시 |
| Model Registry | Loading model rebuild, validation, version, promote, rollback |
| Windows Build | PyInstaller portable build + packaged self-test + Inno Setup installer |

---

## 전체 작업 흐름

### 일반적인 단일 peptide 작업

1. Project / Work Item을 만든다.
2. Sequence를 입력한다.
3. Resin과 scale을 정한다.
4. Loading / coupling chemistry를 확인한다.
5. **Generate**를 누른다.
6. 생성된 Plan을 확인한다.
7. 실제 실험 조건에 맞게 Plan을 수정한다.
8. 수정 후 **Apply Change**를 누른다.
9. Materials / Checklist / Total Materials / Cleavage를 확인한다.
10. 실험을 수행한다.
11. 실제 측정 결과는 **Add Result**에 기록한다.
12. 문제나 intervention은 **Add Issue**에 자연어로 기록한다.
13. 데이터가 쌓이면 Recommendations / Risk & Evidence에서 다음 조건의 근거로 활용한다.

### Generate와 Apply Change를 나눈 이유

- `Generate` = 현재 Setup을 기준으로 Plan을 새로 만든다.
- `Apply Change` = 사용자가 편집한 현재 Plan은 유지하고 연결 결과를 갱신한다.

이 둘을 분리하지 않으면 사용자가 실제 bench workflow에 맞게 Plan을 수정한 뒤 Materials를 다시 계산하는 순간 수정한 내용이 사라질 수 있다.

---

## 빠른 시작

### 권장 환경

- Windows 10 / 11
- 64-bit Python 3.11 또는 3.12
- Tk GUI가 가능한 일반 데스크톱 Python 환경

### 소스 실행

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### 개발/검증 환경

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

### 주요 단축키

| 단축키 | 기능 |
| --- | --- |
| `Ctrl+S` | 저장 |
| `Ctrl+Shift+S` | 다른 이름으로 저장 |
| `Ctrl+O` | Project 불러오기 |
| `Ctrl+N` | Work Item 추가 |
| `Ctrl+D` | Work Item 복제 |
| `Ctrl+G` | Generate |
| `Ctrl+Enter` | Apply Change |
| `Ctrl+E` | 현재 작업 Export |
| `Ctrl+-` | Compact density |
| `Ctrl+0` | Standard density |
| `Ctrl+=` | Comfortable density |
| Work Item `F5` | Refresh |
| Work Item `Esc` | 저장 후 닫기 |

---

## Sequence 입력과 Parser

기본적인 natural sequence와 terminal notation을 지원한다.

```text
GHTYKL
GHTYKL-NH2
-GHTYKL-NH2
Ac-GHTYKL-NH2
AcGHTYKL-NH2
FITC-GHTYKL-NH2
Biotin-GHTYKL-NH2
```

예를 들어:

```text
Ac-GHTYKL-NH2
```

는 개념적으로 다음처럼 분리된다.

```text
N-term : Ac
Core   : G H T Y K L
C-term : NH2
```

### Parser 안전 규칙

- 일반 FASTA형 natural sequence는 residue 단위로 분리한다.
- bracket/catalog 기반 chemical, linker, label, tag는 의미 있는 단위로 유지한다.
- `Ac` compact 표기는 모호하지 않을 때만 인식한다.
- 자연 sequence가 `AC...`로 시작한다는 이유만으로 acetylated peptide로 바꾸지 않는다.
- Ac 이외 N-terminal modifier는 dash로 명확하게 쓰는 것을 권장한다.
- protecting group은 parser가 임의로 만들어내지 않고 catalog/planner layer에서 처리한다.
- natural matching은 필요한 경우 case-insensitive로 처리하지만 D-form/modified token의 의미는 보존한다.

자세한 계약은 [docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md)에 있다.

---

## Plan 생성과 Apply Change

Planner가 다루는 주요 입력은 다음과 같다.

- project / peptide / work item
- sequence
- copies
- synthesis scale
- resin / resin family
- resin loading
- loaded 또는 C-terminal AA
- AA eq
- base eq
- loading time
- coupling reagent / additive / base / solvent
- N-terminal modifier
- branch 설정
- Repeat / Doubling
- cleavage eq / composition / time

### Plan은 단순 출력물이 아니다

Plan은 직접 수정 가능한 작업 상태다.

일반적으로 다음 단계들이 연결된다.

- resin swelling
- loading
- Fmoc deprotection
- pre-coupling wash
- AA / chemical coupling
- post-coupling wash
- repeat coupling / doubling
- N-terminal modification
- final wash
- cleavage / workup 계획

### 기본 process rule 예시

내장 process rule에는 다음과 같은 운영 기본값이 포함된다.

- 20% piperidine / 80% DMF deprotection basis
- 반복 deprotection
- resin family에 따른 swell/loading solvent 처리
- coupling / wash 반복 횟수
- terminal/final wash 처리

이 값들은 **프로그램의 planning default**이며 각 실험실 SOP보다 우선하는 절대 규칙이 아니다.

---

## Materials · Checklist · Batch

### Materials

현재 Plan에서 다음과 같은 재료를 계산할 수 있다.

- Resin
- L-AA
- D-AA
- Non-natural AA
- Branch handle
- Chemical modifier / cap
- Label / Tag / Linker
- Coupling reagent
- Catalyst / Additive
- Base
- Solvent
- Deprotection reagent
- Cleavage component
- 필요한 경우 workup material

MW, density, volume basis가 존재하면 적절한 g/mg/mL 계산을 사용한다. source data에서 unit이 확인되지 않은 값은 임의로 mL/L 등으로 바꾸지 않는 방향이다.

### Batch material 표시 순서

V5의 combined material table은 다음 순서를 따른다.

1. L-AA
2. D-AA
3. Non-natural AA
4. Chemical

각 그룹 내부는 알파벳 순으로 정리한다.

Chemical 그룹에는 modifier/cap, tag, label, terminal chemical-type unit 등이 포함될 수 있다.

**Fmoc-Cit-OH는 Non-natural AA**로 분류한다.

### Checklist

Plan에서 전체 checklist와 짧은 step 중심 view를 생성한다. 이는 operator 편의 기능이며 GMP batch record 또는 기관 표준 문서를 자동 대체하는 용도는 아니다.

### Batch Manager

여러 peptide를 동시에 계산할 수 있으며, selected peptide의 Plan/Materials/Checklist와 전체 Batch Total Materials를 함께 볼 수 있다.

---

## Loading Advisor

V5 Loading Advisor의 목적은 ML 용어를 보여주는 것이 아니라 실제 bench 질문을 해결하는 것이다.

```text
Target Loading (mmol/g)
        ↓
Recommended AA eq
        ↓
Expected Loading
        ↓
Expected Range
        ↓
Confidence / Evidence
        ↓
Apply
```

### 중요한 입력/근거

- Resin
- 같은 loaded/C-terminal AA
- AA eq
- Base eq
- Loading time
- 실제 Measured Loading (`mmol/g`)

### Evidence 우선순위

1. Verified measured loading
2. Same resin + same loaded/C-terminal AA
3. 관측 범위 안의 bounded interpolation
4. 명시적으로 만들어진 model의 cross-check/support
5. Verified가 부족한 경우 Parsed historical fallback
6. 근거가 부족하면 `INSUFFICIENT EVIDENCE`

### 왜 extrapolation을 막는가

소수의 실험값만 가지고 목표 loading을 맞춘다고 무리하게 범위 밖을 예측하면 정밀해 보이는 잘못된 숫자가 나오기 쉽다.

그래서 V5는 가능한 경우 **실제로 관측된 범위 안에서만 inverse recommendation**을 수행하고, 서로 다른 resin/AA를 단순히 N을 늘리기 위해 섞지 않는다.

### Measured Loading 기록

Loading 화면에서 실제 measured loading을 기록하면 현재 Planner가 알고 있는 조건과 Run 정보를 자동으로 붙일 수 있다.

### Loading Model Registry

Model rebuild는 명시적이다.

현재 조건:

- Verified measured loading만 사용
- 최소 12개 eligible record
- 최소 3개의 distinct measured loading value
- categorical feature: resin, normalized amino acid
- numeric feature: AA eq, base eq, loading time
- Random Forest regression
- cross-validation MAE 기록
- model version 보존
- active model과 candidate 비교
- candidate가 구현된 tolerance보다 현저히 나쁘면 active model을 자동 교체하지 않음
- Promote Candidate / Rollback 가능
- model-only output 자동 Apply 금지

Active model이 있는 상태에서 새 Verified measured loading 결과가 약 5개 쌓이면 rebuild를 권하는 알림을 줄 수 있지만 자동 학습하지는 않는다.

---

## Cleavage Advisor

Cleavage는 **실제 history / operator rule / empirical fallback**을 구분한다.

### Cys hard rule

Sequence에 Cys가 하나라도 있으면 현재 operator rule은 다음과 같다.

```text
TFA equivalent = 100 eq × Cys 개수
```

| Cys 개수 | Cleavage eq |
| ---: | ---: |
| 1 | 100 eq |
| 2 | 200 eq |
| 3 | 300 eq |
| 4 | 400 eq |

중요:

- peptide length와 무관하다.
- length baseline에 `+100 eq × Cys`를 더하는 방식이 아니다.
- Cys rule이 최종 eq를 결정한다.
- manual/operator override가 있으면 또 +100을 중복 추가하지 않는다.
- eq 결정과 cocktail composition 결정은 별도다.
- public generic Cys-sensitive fallback은 현재 TFA/TIS/Water `95/2.5/2.5`를 사용한다.

### Non-Cys empirical baseline

더 강한 eligible evidence가 없는 non-Cys peptide에 대해서는 public-safe monotonic baseline이 존재한다.

| 길이 | TFA eq baseline |
| ---: | ---: |
| 1 | 8 |
| 2 | 10 |
| 3 | 15 |
| 4 | 18 |
| 5 | 20 |
| 6 | 30 |
| 8 | 35 |
| 10 | 45 |
| 12 | 50 |
| 14 | 60 |
| 15 | 80 |
| 18 | 88 |
| 21 | 95 |
| 22+ | 100 |

사이 길이는 monotonic interpolation한다.

이 표는 **V5 empirical software baseline**이지 SPPS의 보편적 화학 법칙이 아니다.

### Cleavage evidence 원칙

- exact/repeated history가 있으면 generic fallback보다 우선할 수 있다.
- Public에는 private exact-sequence anchor file을 넣지 않는다.
- similar-sequence evidence는 참고 근거일 뿐 exact observation으로 둔갑시키지 않는다.
- unit이 없는 usage 값은 임의로 mL/L로 추정하지 않는다.
- 여러 product가 섞인 aggregate usage는 automatic scaling의 직접 근거로 쓰지 않는다.
- cleavage cocktail과 precipitation/workup은 분리한다.

### Ether / n-Hexane

Ethyl Ether와 n-Hexane은 precipitation/workup solvent이며 cleavage cocktail component가 아니다.

---

## Post-cleavage NH4I Rescue

NH4I는 기본 cleavage cocktail 성분이 아니다.

기본값:

```text
Post-cleavage Rescue: None
```

필요 시:

```text
Post-cleavage Rescue: NH4I Reduction
```

현재 operator preset:

| 항목 | 기본값 |
| --- | ---: |
| NH4I | peptide 대비 2 eq |
| 최종 농도 | 0.2 M |
| 반응 시간 | 1 h |
| solvent context | TFA / DW |

Program은 peptide scale을 기준으로 NH4I mmol, mg, final solution volume을 계산한다.

**0.2 M 초과는 precipitation 가능성 때문에 block/warn**한다.

Met이 있다는 이유만으로 자동 적용하지 않는다. Oxidation 또는 관련 impurity가 실제로 관찰되었을 때 operator가 선택하는 rescue workflow다.

---

## Recommendations & Lab History

V5에서는 이 창을 daily workflow와 advanced review로 분리했다.

### Recommendations

- Loading
- Cleavage
- All Conditions

### Advanced

- History
- Risk & Evidence
- Data Health

History 안에서는 다음 record를 확인할 수 있다.

- Issues
- Loading
- Cleavage
- Sequence STD
- Cleavage Usage
- Outcomes

### Add Result

사용자는 **실제로 측정한 값**만 넣는 것을 목표로 한다. 이미 Planner가 알고 있는 조건은 자동으로 snapshot에 붙인다.

예:

- Measured Loading
- Yield
- Purity
- Crude weight
- Outcome
- Note

### Add Issue

문제는 자유문장으로 적을 수 있다.

원문을 그대로 보존하면서 가능한 경우 다음을 구조화한다.

- stage
- issue_type
- position
- residue
- severity
- action_taken
- resolution
- confidence
- parse_status
- parser_version
- detected_language

애매한 문장은 `needs_review`로 남겨 ML/risk 데이터에 잘못 들어가는 것을 막는다.

---

## Natural-language Issue Log

한국어, 영어, 혼합 입력을 처리한다.

인식 가능한 대표 issue:

- Kaiser / chloranil 이상
- precipitation failure / partial precipitation
- resin clumping / aggregation
- oxidation
- incomplete deprotection
- incomplete coupling
- poor swelling
- filtration difficulty
- reagent solubility
- side product
- low crude recovery
- cleavage problem
- equipment / process problem

대표 action:

- Repeat coupling
- Repeat deprotection
- Longer reaction
- Solvent change
- Reagent change
- Additional wash
- Re-cleavage / extended cleavage
- Re-precipitation
- NH4I reduction
- Manual intervention

Issue가 있다고 무조건 실패로 분류하지 않는다.

예를 들어:

```text
Incomplete coupling
      ↓
Repeat coupling
      ↓
Resolved
      ↓
Final purity 97%
```

이라면 “문제는 있었지만 해결된 성공적 outcome”으로 남을 수 있다.

---

## Run 추적성

새로운 독립 Run 시스템을 하나 더 만들지 않고 기존 Work Item / Run 구조를 사용한다.

실험 record에는 다음 연결값을 가질 수 있다.

```text
work_item_id
run_id
```

사용자가 기술적인 ID를 매번 직접 입력하는 방식이 아니라, 현재 active run을 Planner가 알고 있으면 자동으로 연결하는 것이 목표다.

그래서 나중에 “이 측정 loading이 정확히 어떤 조건에서 나온 것인가?”를 추적할 수 있다.

---

## Evidence / ML 정책

### 데이터 상태

| 상태 | 의미 |
| --- | --- |
| Verified | operator가 확인한 실제 실험 근거 |
| Parsed | import/parsing되었지만 더 강한 review가 필요한 기록 |
| Incomplete | 보존하지만 특정 target/학습에 필요한 정보가 부족 |
| Excluded | 삭제하지 않고 audit용으로 남기되 추천/학습에서 제외 |

### 다른 근거 종류

- Operator rule
- Empirical estimate
- Model output
- Literature / chemistry reference

이들을 Verified 실험값과 동일하게 취급하지 않는다.

### 일반적인 추천 우선순위

1. 반복되고 성공적인 relevant history
2. exact bottle/sequence/product evidence
3. coherent category evidence
4. observed range 내 bounded interpolation
5. chemistry/risk reference 또는 empirical fallback
6. insufficient evidence

### 의도적으로 하지 않는 것

- 관측 범위 밖 extrapolation을 신뢰 가능한 값처럼 제시
- 서로 다른 resin/AA를 단순히 sample 수 늘리려고 섞기
- import record 자동 Verified 승격
- Generate된 Plan을 실제 실험 결과로 사용
- Result 입력 때마다 자동 retrain
- Model-only output 자동 Apply
- unit 없는 숫자를 mL/L로 추측
- 서로 다른 실험을 섞어 가짜 historical cocktail 생성

---

## Public 데이터 정책

Public GitHub판은 **data-sanitized build**다.

포함:

- experimental schema
- record/import UI
- recommendation logic
- similarity / risk / evidence 기능
- model management
- public-safe generic rule
- 빈 experimental seed 안내

제외:

- 내부/개인/회사 실험 history
- private product-to-sequence mapping
- private exact sequence cleavage anchor
- 공개하면 안 되는 operator-specific experimental record

사용자는 자신이 사용할 권한이 있는 데이터를 로컬에서 추가해야 한다.

자세한 내용은 [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)를 참고한다.

---

## Runtime 데이터

Public build의 사용자 생성 데이터는 source repository 밖에 둔다.

Windows core runtime 경로 기준:

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

여기에는 상황에 따라 다음이 들어갈 수 있다.

- Project / Session
- Experimental SQLite DB
- Imported lab data
- Model file / registry
- Runtime log
- Export / output
- 분석파일 link metadata

이 파일들은 사용자가 공개를 명시적으로 검토하지 않았다면 GitHub에 commit하면 안 된다.

`.gitignore`에는 sqlite, private data directory, build output, archive, log, venv 등 일반적인 runtime/generated artifact 차단 규칙이 포함되어 있다.

---

## 저장소 구조

```text
SPPS-PLANNER/
├─ main_launcher.py
├─ suite_gui/
├─ apps/spps_planner_app/
│  ├─ spps_planner/
│  └─ data/
├─ peptiforg_core/
├─ tests/
├─ tools/
├─ docs/
├─ assets/
├─ installer/
├─ BUILD_EXE_ONLY.bat
├─ BUILD_INSTALLER.bat
├─ INSTALL_BUILD_TOOLS_AND_BUILD.bat
├─ SPPS_Planner.spec
├─ requirements.txt
├─ requirements-dev.txt
├─ PUBLIC_DATA_POLICY.md
├─ CONTRIBUTING.md
├─ CITATION.cff
├─ LICENSE
├─ VERSION
└─ README.md
```

### 주요 코드 위치

| 영역 | 파일 |
| --- | --- |
| Entry / release | `main_launcher.py`, `suite_gui/release.py` |
| GUI / controller | `suite_gui/controller.py`, `suite_gui/classic_base.py` |
| Generate / Apply | `suite_gui/synthesis_workflow.py`, `suite_gui/modules/plan_workflow.py` |
| Project / State | `suite_gui/project_workflow.py`, `suite_gui/peptide_item_state.py` |
| Experimental DB | `suite_gui/experimental_data.py` |
| Loading/Cleavage Advisor | `suite_gui/ml_advisor_v5.py`, `suite_gui/empirical_cleavage_v5.py` |
| Model Registry | `suite_gui/model_registry_v5.py` |
| Issue Parser | `suite_gui/natural_language_issue_v5.py` |
| Recommendation UI | `suite_gui/modules/experimental_data_panel.py` |
| NH4I / Cleavage UI | `suite_gui/modules/cleavage_panel.py` |
| Engine | `apps/spps_planner_app/spps_planner/engine.py` |
| Parser | `apps/spps_planner_app/spps_planner/parser.py` |

더 자세한 내용은 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참고한다.

---

## Windows 빌드

### Portable EXE

```bat
BUILD_EXE_ONLY.bat
```

결과:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

### Installer

Inno Setup이 있는 상태에서:

```bat
BUILD_INSTALLER.bat
```

결과:

```text
installer\output\SPPS_Planner_Setup_V5.0.0.exe
```

### Build tool 확인/설치부터 한 번에

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

이 workflow는 단순히 EXE 파일이 생성되었다는 것만 확인하지 않고 packaged runtime self-test와 release contract를 통해 실제 packaged app이 필요한 모듈을 정상적으로 포함했는지 확인하는 방향이다.

Windows release checklist는 [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md)에 있다.

---

## 검증과 회귀 테스트

### 전체 Release Verification

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

여러 번 반복 검증:

```bat
python tools\verify_release.py --passes 5
```

Release verifier는 다음을 확인한다.

- 필수 release file
- V5.0.0 version identity
- active controller contract
- Windows release contract
- runtime monkey-patch/rebinding audit
- source compile
- 전체 pytest suite

### Windows contract

```bat
python tools\verify_windows_release.py
```

### Active release monkey-patch audit

```bat
python tools\audit_monkey_patches.py --active-release
```

### V5 주요 회귀 테스트 영역

- parser / sequence
- Generate / Apply Change
- resin/loading
- C-terminal behavior
- Repeat / Doubling
- Materials / Checklist / Totals
- Project / Session persistence
- Batch
- Custom DB
- Cys 100 eq-per-Cys
- Cys eq double-add 방지
- empirical cleavage
- target-loading bounded inverse
- Loading model rebuild/promote/rollback
- active Run linkage
- bilingual issue parsing
- NH4I ≤0.2 M
- DB initialization fast path
- Public release/data contract

---

## 성능 설계

V5.0.0은 **Recommendations / Lab History** 창을 열 때 불필요한 반복 DB 작업을 줄이고, 무거운 history 화면이 모두 준비될 때까지 창 표시를 막지 않도록 동작 순서를 개선했다.

목표는 다음과 같다.

```text
Button click
   ↓
창이 먼저 보임
   ↓
필요한 recommendation/history 내용이 이어서 로드됨
```

기존 Recommendation, History, Risk & Evidence, Data Health 기능은 그대로 유지된다.

---

## 과학적 범위와 한계

SPPS Planner는 연구/계획 지원 도구다.

사용자는 반드시 다음을 직접 검토해야 한다.

- sequence / modification
- protecting group 및 bottle identity
- resin / loading
- scale 단위
- AA / reagent eq
- 농도
- coupling / deprotection chemistry
- Repeat / Doubling
- cleavage composition / amount
- workup / precipitation
- reactor / equipment volume 및 호환성
- SDS / 기관 안전규정
- 실제 실험 검증

### Empirical rule은 universal law가 아니다

Cys hard rule, non-Cys length curve, generic cocktail fallback, NH4I rescue preset은 현재 software/operator rule이다. 모든 peptide/scale/resin/보호기에 보편적으로 최적인 조건이라는 의미가 아니다.

### Historical data에는 bias가 있을 수 있다

실험 이력은 기록된 데이터에 의존한다. operator effect, scale effect, 분석법 변경, selection bias, 누락 등으로 인해 단순한 상관관계를 causal optimum으로 해석하면 안 된다.

### Model도 advisory다

Cross-validation MAE가 좋더라도 새로운 chemistry에 대한 보장은 아니다. Model은 판단을 돕는 근거 중 하나다.

---

## 문서 안내

### 시작용

- [README.md](README.md) — English full overview
- [README_KO.md](README_KO.md) — 한국어 full overview
- [docs/USER_MANUAL_KO.md](docs/USER_MANUAL_KO.md) — 한국어 사용자 매뉴얼
- [docs/USER_MANUAL_EN.md](docs/USER_MANUAL_EN.md) — English user manual

### Technical

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md)
- [docs/SPPS_REAGENT_DATABASE_SCHEMA.md](docs/SPPS_REAGENT_DATABASE_SCHEMA.md)
- [docs/V5_DECISION_SUPPORT_EN.md](docs/V5_DECISION_SUPPORT_EN.md)
- [docs/V5_DECISION_SUPPORT_KO.md](docs/V5_DECISION_SUPPORT_KO.md)
- [docs/DATA_SYSTEM_KO.md](docs/DATA_SYSTEM_KO.md)
- [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md)

### Policy / Release

- [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [LICENSE](LICENSE)
- [CITATION.cff](CITATION.cff)

---

## 기여

기여는 환영하지만 기존 release contract를 보존해야 한다.

특히 다음은 피한다.

- 프로그램 전체 재작성
- 기존 기능을 단순화된 별도 화면으로 대체
- runtime monkey patch
- placeholder / dummy / fake training data
- 실제 reagent identity 무시
- plan condition을 measured experimental truth로 취급
- Result 입력 시 자동 model rebuild
- confidential experimental data를 Public에 포함

Calculation/recommendation behavior를 바꾸는 PR은 최소한 다음을 설명하는 것이 좋다.

1. 기존 문제
2. 기존 동작
3. 변경 동작
4. 변경 이유
5. 어떤 test로 regression을 막았는지

자세한 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있다.

---

## 인용

SPPS Planner 또는 SPPS Planner에서 생성된 결과/워크플로/수정본을 학술 작업에 사용하는 경우 포함된 라이선스의 citation/attribution 조건을 확인해야 한다.

권장 repository citation:

> Woo, S. **SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.** GitHub repository, Version 5.0.0. https://github.com/SanghunWoo-23/SPPS-PLANNER

[CITATION.cff](CITATION.cff)를 포함했기 때문에 GitHub의 **Cite this repository** 기능에서도 citation metadata를 사용할 수 있다.

향후 release DOI가 생성되면 해당 release DOI도 함께 사용한다.

---

## 라이선스

이 저장소는 **SPPS Planner Public Academic Citation License Version 1.0**을 사용한다.

학술·교육·연구·portfolio review·비상업적 사용을 허용하는 custom public-source license이며, 인용/attribution 조건이 있다.

현재 라이선스는 OSI-approved open-source license가 아니므로 라이선스가 변경되지 않는 한 “OSI 오픈소스”라고 표현하면 안 된다.

자세한 내용은 [LICENSE](LICENSE)를 반드시 확인한다.

---

## 문제 해결

### 소스 실행이 안 됨

```bat
python --version
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

지원 Python 버전과 dependency 설치 상태를 확인한다.

### 창이 안 뜸

Tk가 포함된 일반 desktop Python 환경을 사용한다. Headless 서버 환경은 일반 operator 사용 환경이 아니다.

### EXE는 생겼는데 build validation이 실패함

파일이 생겼다는 이유만으로 성공으로 보지 않는다.

```bat
python tools\verify_release.py
python tools\verify_windows_release.py
```

첫 실패 항목부터 확인한다.

### Public에서 Recommendation history가 비어 있음

정상이다. Public은 private seed 없이 시작한다. 자신의 승인된 실험 데이터를 기록/import해야 history-driven recommendation이 생긴다.

### Loading model이 없음

현재 최소 12개의 eligible Verified measured loading record와 3개의 distinct target value가 필요하다.

### Loading target을 넣었는데 Apply가 안 됨

관측 범위 밖 extrapolation이 필요하거나 충분한 eligible condition이 없으면 evidence는 보여주되 Apply를 막을 수 있다.

### Cys peptide에서 cleavage eq가 너무 커 보임

현재 V5 rule이 `100 eq × Cys count`인지 확인한다.

### NH4I >0.2 M가 막힘

의도된 동작이다. 현재 operator protocol에서 0.2 M 초과는 precipitation 위험 때문에 block/warn한다.

### Import한 숫자에 mL가 자동으로 안 붙음

source에 unit이 없으면 임의로 추측하지 않는다. operator review가 필요하다.

---

## FAQ

### 자동 합성 장비 controller인가?

아니다. 현재 release는 planning, calculation, traceability, decision-support desktop application이다.

### 자동으로 최적 조건을 찾아주는가?

근거가 있으면 historical evidence, bounded interpolation, empirical rule, explicit local model을 사용해 추천할 수 있다. 하지만 무근거 extrapolation을 “최적화 결과”처럼 단정하지 않는다.

### Result 하나 추가하면 바로 재학습하는가?

아니다. Rebuild는 명시적으로 실행한다.

### 실험 history가 하나도 없어도 쓸 수 있는가?

그렇다. Core Planner와 public-safe fallback은 experimental DB가 비어 있어도 동작하도록 설계되어 있다.

### 내 실험 데이터를 import할 수 있는가?

가능하다. 단, 사용/공개 권한이 있는 데이터만 사용해야 한다.

### Public GitHub에 내부 실험 데이터가 포함되는가?

의도적으로 포함하지 않는다.

### Model 결과가 자동으로 Plan에 적용되는가?

아니다. Model-only output 자동 Apply를 막는 방향이다.

### 왜 History/Data Health가 Advanced에 있는가?

중요하지만 매번 실험할 때마다 조작하는 메뉴는 아니기 때문이다. V5 primary workflow는 Add Result, Add Issue, 현재 recommendation을 우선한다.

### 왜 raw note를 보존하는가?

Parser가 틀릴 수 있기 때문이다. 나중에 구조화 결과를 수정하더라도 operator가 실제로 적었던 원문을 잃지 않기 위해서다.

### 오픈소스인가?

소스는 공개되어 있지만 현재는 custom academic citation license이며 OSI-approved license가 아니다.

---

## 버전

현재 Public release:

```text
V5.0.0
```

`VERSION`, `VERSION.txt`, release title과 Windows release metadata가 verification tool로 검사된다.

---

<div align="center">

**SPPS Planner V5.0.0**  
Plan은 편집 가능하게. Evidence는 출처를 잃지 않게. Model은 조언자로.

</div>
