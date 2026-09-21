<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner v6.0.0

**고체상 펩타이드 합성(SPPS)의 계획·계산·기록·실험 근거 기반 의사결정을 지원하는 Windows 중심 데스크톱 프로그램**

Sequence parsing · Editable Plan · Materials · Checklist · Batch · Loading Advisor · Cleavage Advisor · Experimental History

[![Release](https://img.shields.io/badge/release-v6.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)
[![License](https://img.shields.io/badge/license-Academic%20%2F%20Non--commercial-6B7280?style=for-the-badge)](LICENSE)

**[English README](README.md) · [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md) · [English User Manual](docs/USER_MANUAL_EN.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)**

Repository: **SanghunWoo-23/SPPS-PLANNER**

</div>

> **현재 공개 릴리스: v6.0.0.** 이 Public 패키지는 검증된 V6 R19 소스 라인을 기준으로 하며, 프로그램 기능 코드는 포함하지만 **Private 실험 이력, Private seed, 원본 실험 사진, 로컬 실험 DB는 포함하지 않습니다.**

---

## SPPS Planner란?

SPPS Planner는 **고체상 펩타이드 합성(SPPS)** 조건을 계획하고, 계산 결과와 실제 실험 기록을 연결하기 위한 데스크톱 작업 도구입니다.

```text
Peptide / Project 설정
        ↓
Sequence + Modifier + Resin + Scale + Chemistry
        ↓
Generate
        ↓
Editable Plan
 ├─ Materials
 ├─ Checklist
 ├─ Total Materials
 ├─ Cleavage
 └─ Export / Batch
        ↓
실제 합성
        ↓
Add Result / Add Issue
        ↓
Run과 연결된 로컬 실험 근거
        ↓
Loading / Cleavage Recommendation
```

프로그램은 합성 조건을 자동으로 단정하는 블랙박스를 목표로 하지 않습니다. 사용자가 편집한 Plan을 실제 상태로 유지하고, **실측 근거 / 보간 / 화학 기본값 / 모델 추정**을 가능한 한 구분해서 보여주는 것이 핵심 설계 원칙입니다.

---

## v6.0.0 주요 기능

### 1. 편집 가능한 SPPS Plan

- Sequence, resin, scale, loading, coupling, terminal setting을 기반으로 Plan 생성
- 생성된 Plan 직접 수정
- **Apply Change**로 현재 보이는 수정 Plan을 유지하면서 Materials/Checklist 등 연동 결과 재계산
- 여러 peptide Work Item 및 Batch 계산 지원

### 2. 다양한 building block 인식

- 표준 L-amino acid
- D-form amino acid
- 실제 Loading 자료에 기반한 `Cit`, `Hyp`, `Dab` 등의 special/non-natural identity
- Linker, label, tag, N-terminal modifier 및 terminal chemistry
- 보호기 형태가 다른 building block을 임의로 같은 물질로 합치지 않음

### 3. Loading Advisor

Loading Recommend는 **실험 데이터 우선 + 보수적 판단**을 기본으로 합니다.

- 직접 추천 근거는 **동일 resin + 동일 normalized loaded-AA identity**만 사용
- D-form과 L-form 데이터를 분리
- non-natural AA의 이름을 인식한다고 해서 근거 `n`이 자동 증가하지 않음
- 동일 조건 반복 실험의 실제 관측 범위가 target을 포함하면 `OBSERVED REPEATED CONDITION` 사용 가능
- 관측 범위 내부에서만 bounded interpolation
- 관측 범위 밖 extrapolation을 실험 근거처럼 표시하지 않음
- 실측 근거가 없을 때 사용하는 `CHEMISTRY DEFAULT`는 예측값과 분리 표시
- 근거 데이터 수, Verified/Parsed, min/median/max, 날짜 범위, 반복성, capping, source locator, 근접 실험 조건 표시

현재 identity normalization 예시는 다음과 같습니다.

```text
Cit          -> Fmoc-Cit-OH
Hyp          -> 실제 관측 identity가 Fmoc-Hyp(tBu)-OH인 경우 해당 형태
Dab          -> Fmoc-Dab(Boc)-OH
D-Leu / dL   -> Fmoc-D-Leu-OH
D-Phe / dF   -> Fmoc-D-Phe-OH
D-His(Trt)   -> Fmoc-D-His(Trt)-OH
```

Gly은 achiral로 취급하며 임의의 `D-Gly` identity를 만들지 않습니다.

### 4. Cleavage Advisor

- Cleavage cocktail과 equivalent 양을 분리해서 관리
- 기존 Cys hard rule 유지: 자동 적용 시 **TFA eq = 100 × Cys count**
- Cys rule에 peptide-length baseline을 중복 가산하지 않음
- NH4I reduction은 일반 cleavage cocktail과 분리된 post-cleavage rescue workflow
- Met이 있다는 이유만으로 NH4I를 자동 삽입하지 않음

### 5. 실험 기록과 추적성

- Loading / Cleavage / Outcome / Issue 등 실험 기록 저장
- 가능한 경우 active Run 및 Planner condition snapshot과 연결
- 원본 raw text를 보존하면서 검색용 canonical key를 별도 사용
- 애매하거나 provisional인 기록을 강한 근거로 자동 승격하지 않음
- 사용자가 명시적으로 내보내거나 공개하지 않는 한 로컬 데이터는 로컬에 유지

### 6. 명시적인 model workflow

- Loading model rebuild는 자동이 아니라 명시적 실행
- Candidate validation / promotion / rollback 지원
- Result를 추가했다고 모델이 몰래 재학습되지 않음

---

## 빠른 시작

### 권장 환경

- Windows 10 / 11
- 64-bit Python 3.11 또는 3.12
- Tk 사용이 가능한 일반 데스크톱 Python 환경

### 소스에서 실행

Repository root에서:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### 개발 / 검증 환경

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

추가 검증:

```bat
python tools\verify_v6_integrity.py
python tools\verify_windows_release.py
```

---

## 기본 사용 흐름

1. Peptide / Work Item을 설정합니다.
2. Sequence, resin, scale, loading, coupling system 등을 입력합니다.
3. **Generate**로 새 Plan을 만듭니다.
4. 필요한 경우 Plan을 직접 수정합니다.
5. **Apply Change**로 수정된 현재 Plan을 기준으로 연결 계산을 갱신합니다.
6. Materials / Checklist / Total Materials / Cleavage를 검토합니다.
7. 실제 합성 후 **Add Result** 또는 **Add Issue**를 기록합니다.
8. Recommendations & Lab History에서 누적 근거를 검토합니다.

### Generate와 Apply Change의 차이

| 기능 | 의미 |
| --- | --- |
| **Generate** | 현재 Setup 입력으로 새로운 Plan을 생성 |
| **Apply Change** | 현재 화면에서 수정된 Plan을 유지한 채 연동 계산만 다시 수행 |

이 구조는 Plan을 수동으로 수정한 뒤 Materials만 다시 계산했을 때 원래 Plan으로 되돌아가는 문제를 방지합니다.

---

## Loading Recommendation 원칙

Loading Advisor는 다음 순서를 따릅니다.

1. 동일 resin + 동일 loaded-AA identity의 실제 이력을 우선 사용
2. outlier로 표시된 기록은 evidence-driven inversion에서 제외
3. 동일 조건 반복 측정 범위 안에 target이 있으면 실제 반복 조건을 우선 고려
4. 관측된 범위 내부에서만 bounded interpolation
5. broad similarity는 진단용 context로만 사용
6. 정의된 경우에만 명시적으로 `CHEMISTRY DEFAULT` fallback 사용
7. 범위 밖에서는 가짜 실험 예측을 만드는 대신 insufficient/out-of-range 상태 표시

화면에서는 다음 provenance를 구분합니다.

- **Exact experimental match**
- **Bounded interpolation**
- **Default fallback**
- **Insufficient / outside observed range**

D-form 및 special/non-natural building block은 **인식 가능 여부와 실험 근거 여부를 분리**합니다. 따라서 identity는 정상 인식되더라도 exact-history `n=0` 또는 `n=1`로 표시될 수 있습니다.

---

## Batch Manager / Project Manager 연동

Batch Manager는 **Project Manager의 peptide sequence를 읽어 합성기용 stock/solution 준비량을 계산하는 도구**입니다. R19부터 Project Manager의 DIC/HOBt/HBTU 선택, project별 reagent eq, resin/loading 조건을 합산하지 않습니다. 준비량 계산은 Batch Manager 상단의 **Solution prep defaults**만 사용합니다.

- Project Manager에서 실제 sequence가 있는 항목만 읽습니다.
- `Copies`는 합성 column 수를 반영하며, 계산 scale은 Batch Manager의 `Scale mmol` 기본값을 사용합니다.
- AA stock은 `Scale mmol × AA eq ÷ AA conc`를 기준으로 계산합니다.
- HBTU/NMP stock은 `Scale mmol × HBTU eq ÷ HBTU conc`를 기준으로 계산합니다.
- `Round-up mL`과 `Extra reserve mL`를 적용해 실제 준비 부피를 산출합니다.
- Project Manager에 DIC/HOBt 조건이 저장되어 있어도 Batch Manager에 DIC/HOBt 사용량으로 나타나지 않습니다.
- 빈/default placeholder 및 sample/demo sequence는 계산하지 않습니다.
- **Refresh totals**는 현재 sequence와 prep defaults를 다시 계산합니다.
- Autosave와 기존 Project 이력은 그대로 보존합니다.


## Public 데이터 정책

GitHub용 Public 패키지는 **data-sanitized build**입니다.

다음 데이터는 의도적으로 포함하지 않습니다.

- 내부/Private Loading 실험 이력
- Private Cleavage 이력
- 기밀 product-sequence mapping
- 원본 실험 사진 및 Private source manifest
- 로컬 SQLite DB
- Private 데이터로 학습된 model artifact
- 사용자 export / log / runtime data

Public 버전은 비어 있는 public-safe experimental seed에서 시작하며, 사용자는 자신이 사용 권한을 가진 데이터만 로컬로 기록하여 근거 DB를 구축할 수 있습니다.

Windows에서 Public runtime 데이터는 repository 바깥의 다음 user-data 영역을 기반으로 저장됩니다.

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

DB, model, export, log 등을 GitHub에 올리기 전에는 반드시 [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)를 확인하십시오.

---

## 프로젝트 구조

```text
SPPS-PLANNER/
├─ main_launcher.py
├─ suite_gui/
├─ apps/spps_planner_app/
├─ tests/
├─ tools/
├─ docs/
├─ assets/
├─ installer/
├─ requirements.txt
├─ requirements-dev.txt
├─ SPPS_Planner.spec
├─ BUILD_EXE_ONLY.bat
├─ BUILD_INSTALLER.bat
├─ LICENSE
└─ CITATION.cff
```

상세한 모듈 ownership 및 release boundary는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참고하십시오.

---

## Windows 빌드

PyInstaller / Inno Setup 기반 release 경로가 포함되어 있습니다.

```bat
BUILD_EXE_ONLY.bat
BUILD_INSTALLER.bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

배포 전 release verification을 실행하고 [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md)를 확인하는 것을 권장합니다.

---

## v6.0.0 검증 결과

최종 Public ZIP을 별도 디렉터리에 다시 푼 fresh-unzip 상태에서 검증했습니다.

- 전체 Public headless pytest: **370 passed / 28 skipped**
- 전체 Public Real-Tk/Xvfb pytest: **395 passed / 3 skipped**
- R19 sequence-driven Batch prep 실제 Tk 회귀: **PASS**
- `tools/verify_v6_integrity.py`: **PASS**
- `tools/verify_windows_release.py`: **PASS**
- Public experimental seed: 문서용 `README.md`만 포함
- Public SQLite/DB: **0개**
- ZIP integrity: **PASS** (`testzip = None`)
- R19 Batch solution-prep 분리 후에도 chemistry engine의 golden behavior 유지

Public/Private 대응 빌드의 공유 소스 parity 역시 release validation에서 확인했으며, Private 실험 데이터는 Public 패키지로 이동하지 않습니다.

---

## 과학적 사용 범위와 한계

SPPS Planner는 **연구 계획, 계산, 기록, 우선순위 설정 및 의사결정 보조**를 위한 프로그램입니다.

다음을 대체하지 않습니다.

- 승인된 SOP
- SDS 및 기관 안전 규정
- 숙련된 작업자의 판단
- 검증된 분석법
- 실제 합성 결과 확인
- 필요한 경우의 GMP/GLP 공식 문서

특히 Recommendation은 표시된 provenance를 함께 확인해야 합니다. Chemistry default, empirical rule, interpolation, model estimate, 실제 반복 실험은 서로 같은 수준의 근거가 아닙니다.

---

## 문서

| 문서 | 내용 |
| --- | --- |
| [README.md](README.md) | English project overview |
| [docs/USER_MANUAL_KO.md](docs/USER_MANUAL_KO.md) | 한국어 사용자 매뉴얼 |
| [docs/USER_MANUAL_EN.md](docs/USER_MANUAL_EN.md) | English user manual |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 구조 / ownership |
| [docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md) | Sequence parser contract |
| [docs/SPPS_REAGENT_DATABASE_SCHEMA.md](docs/SPPS_REAGENT_DATABASE_SCHEMA.md) | Reagent DB schema |
| [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md) | Public/Private 데이터 경계 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| [CHANGELOG.md](CHANGELOG.md) | 변경 이력 |
| [RELEASE_NOTES_V6.0.0.md](RELEASE_NOTES_V6.0.0.md) | v6.0.0 공개 릴리스 노트 |

V5 decision-support 문서와 과거 개발 체크포인트 문서는 배포 루트에서 제거하여 파일 구성을 정리했으며, 공개 변경 이력은 CHANGELOG에 유지합니다.

---

## Citation

학술 연구에서 SPPS Planner를 사용한 경우 software와 해당 tagged release/DOI(있는 경우)를 인용해 주십시오.

권장 표기:

> Woo, S. **SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.** Version 6.0.0. GitHub repository, 2026. https://github.com/SanghunWoo-23/SPPS-PLANNER

GitHub citation 기능을 위한 [CITATION.cff](CITATION.cff)가 포함되어 있습니다.

---

## License

SPPS Planner는 **SPPS Planner Public Academic Citation License**로 배포됩니다.

학술·교육·연구·포트폴리오 검토·비상업적 사용을 허용하는 custom source-available license이며, 조건에 따라 인용이 필요합니다. **OSI 승인 오픈소스 라이선스는 아닙니다.**

자세한 내용은 [LICENSE](LICENSE)를 확인하십시오.

---

## Release notes

공개용 변경 사항은 [RELEASE_NOTES_V6.0.0.md](RELEASE_NOTES_V6.0.0.md), 전체 개발 이력은 [CHANGELOG.md](CHANGELOG.md)를 참고하십시오.
