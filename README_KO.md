<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner 아이콘" width="150">

# SPPS Planner

### 펩타이드 서열을 편집 가능한 합성 계획과 작업 기록으로

**고체상 펩타이드 합성(SPPS)** 계획, 재료량 계산, 다중 펩타이드 관리,
작업자용 기록 출력을 하나로 연결한 데스크톱 프로그램입니다.

[![Release](https://img.shields.io/badge/release-V3.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)
[![Tests](https://img.shields.io/badge/regression_tests-149%20passed-16A34A?style=for-the-badge)](#검증)

**[English](README.md) · [빠른 시작](#빠른-시작) · [주요 기능](#주요-기능) · [Windows 빌드](#windows-빌드) · [코드 구조](docs/ARCHITECTURE.md)**

</div>

---

## 왜 SPPS Planner인가?

SPPS 계획은 서열을 아미노산 질량으로 변환하는 것만으로 끝나지 않습니다.
Resin, loading, coupling chemistry, 반복 반응, deprotection, wash,
terminal modification, cleavage cocktail과 작업자가 직접 수정한 조건이
모두 함께 연결되어야 합니다.

SPPS Planner는 이 흐름을 하나의 프로그램에서 관리합니다.

```text
펩타이드 서열
      ↓
Resin · Scale · Loading · Chemistry
      ↓
직접 편집 가능한 합성 Plan
      ↓
Apply Change
      ↓
Materials · Checklist · Total · Batch · Export
```

## 주요 기능

V3의 단계별 구현 범위와 현재 상태는
[V3 개발 로드맵](docs/V3_DEVELOPMENT_ROADMAP_KO.md)에서 확인할 수 있습니다.

Stage 6/6까지 독립 Work Item 창, 실행 원장, ML, Project → Work Item → Run
데이터 계층과 `Data / HPLC` 작업공간을 구현했습니다. 여러 합성 Run을
분리해 저장하고 HPLC 결과·원본 파일을 연결하며, 전체 데이터를 다중 시트
XLSX로 왕복할 수 있습니다. `Risk Review`는 합성 위험 후보를 근거·영향과
함께 보여주며 실제 검토 데이터 모델이 있을 때만 ML 신호를 추가합니다.
최종 혼합식 UI는 화면 크기에 맞춰 배치되고 세 가지 표시 밀도, 키보드
작업, Windows 고해상도 처리와 완전한 V3 빌드 경로를 제공합니다.

| 영역 | 기능 |
| --- | --- |
| **Project Manager** | 여러 펩타이드 관리, 복제·삭제·순서 이동, 펩타이드별 입력값과 계산 결과 보존 |
| **Sequence 해석** | 말단기, 일반·D형·비천연 아미노산, chemical, modifier, tag, label, linker 인식 |
| **Resin 및 Loading** | Rink Amide 계열, 2-CTC 직접 loading, preloaded `CTC(합성기)`, Wang, HMPB, Sieber Amide, PAL, Tentagel, Manual |
| **합성 Plan** | Coupling·deprotection·wash 단계 생성 및 물질명, MW, 밀도, eq, 시약, 용매, 반복 횟수 직접 편집 |
| **Apply Change** | 수정한 Plan을 서열에서 다시 만들지 않고 현재 보이는 Plan 기준으로 연관 결과 재계산 |
| **Materials** | Resin, 아미노산, coupling reagent, catalyst, base, solvent, modifier, cleavage component 계산 |
| **Doubling 및 반복** | 위치별 doubling과 2회 이상의 반복 반응을 Materials와 Checklist까지 동기화 |
| **실시간 실행 기록** | 단계 상태, 실제 투입량, 현장 Plan 수정, doubling, 사유와 작업자 메모를 append-only 이벤트로 기록 |
| **보상 되돌리기** | 기존 기록을 삭제하지 않고 반대 변경 이벤트를 추가하여 Plan과 연결 결과를 원복 |
| **Cleavage** | Preset 및 사용자 cocktail 조성, 액체·고체 성분의 질량/부피 표시 |
| **Batch Manager** | Region/linker/tag/label 편집, Project 행 동기화, 보호 시약명 기준 펩타이드별·전체 Batch 재료량 통합 계산 |
| **저장 및 출력** | 자동저장과 CSV/XLSX/JSON 출력, Project·Peptide·LOT 정보 기록 |
| **Project 데이터 시스템** | Work Item별 복수 Run, 원자적 JSON, 정상본 백업·복구, 최근 파일, 외부 수정 충돌 방지 |
| **Excel Workbook** | Project/Run/Plan/Event/ML/HPLC/Materials/Total/Checklist/Cleavage/History 다중 시트 왕복과 컬럼 매핑 |
| **HPLC 연결** | 결과·분석조건 CRUD, 검색·정렬, 변경 이력, data/method 파일 경로와 SHA-256 무결성 metadata |
| **Custom DB** | 사용자 물질의 분류, MW, 밀도, 메모 추가·수정·삭제 |
| **실데이터 ML** | 실행 원장에서 feature를 생성하고 검토된 수율·순도·실패·doubling 결과가 5건 이상일 때 실제 모델 학습·예측 |
| **ML 데이터 검토** | Work Item별 결과 revision, 포함/제외 사유, 불변 dataset snapshot·fingerprint·manifest 관리 |
| **합성 위험 검토** | Aspartimide·aggregation·difficult coupling·산화/보호기·실행 이력 규칙과 실제 데이터 ML 신호, Run별 revision/확인 이력 |
| **최종 UI·Windows** | 반응형 창, 세 가지 표시 밀도, 단축키, DPI 처리, V3 EXE/Installer metadata와 자동 빌드 검증 |
| **V2 기준 반응속도** | 자동저장·live sync 병합, Batch 결과 캐시, 항목당 단일 Plan 계산, 연결 결과 일괄 렌더링 |

## 작업자 중심 동작

- **Generate**는 현재 입력값에서 Plan, Materials, Checklist, Total Materials를 한 번에 생성합니다.
- **Apply Change**는 직접 수정한 Plan을 보존해 연결 결과를 갱신하며, Cleavage 적용은 기존처럼 이 동작에서만 수행합니다.
- 빈 서열에 가짜 펩타이드나 예시 Plan을 넣지 않습니다.
- Chemistry preset 버튼은 조건만 변경하고 Plan을 멋대로 생성하지 않습니다.
- `2-CTC` 직접-loading 행은 일반 DIC/HOBt coupling으로 잘못 변환하지 않습니다.
- 과거 저장값 `CTC(합성용)`은 `CTC(합성기)`로 호환됩니다.
- Work List 항목을 더블클릭하고 `Run / Corrections`에서 단계 상태와 실제
  투입량을 기록할 수 있습니다.
- 현장 수정과 doubling은 사유가 필수이며, 되돌리기도 새 이력으로 남습니다.
- `Outcome / ML`에서 실제 결과를 검토 저장하며, 제외 데이터에는 사유가 필수입니다.
- 학습 데이터가 5건 미만이거나 분류값이 한 종류뿐이면 모델을 만들지 않습니다.
- 수율·순도·실패·doubling 결과 컬럼은 입력 feature에서 제거하여 결과 누출을 막습니다.
- `Data / HPLC`에서 새 Run을 만들거나 과거 Run을 활성화할 수 있습니다.
- 불러온 Project 파일이 외부에서 변경되면 덮어쓰지 않고 Reload 또는 Save As를 요구합니다.
- 손상된 JSON은 마지막 정상 `.bak`에서 복구하며, HPLC 삭제도 변경 이력에서 보존됩니다.
- `Risk Review`의 rule score는 실패 확률이 아니며, 모든 finding은 자동 적용 없이 근거·영향·검토 권고를 표시합니다.
- ML 위험 신호는 유효한 실제 검토 데이터 모델이 있을 때만 표시되고 dataset fingerprint까지 추적됩니다.
- 정적 unit-name 정규화 메서드는 최종 Classic controller에서도 정적 메서드로 유지되어 Generate 시작 시 인자 오류가 발생하지 않습니다.
- 일반·D형·비천연 아미노산은 Plan 선택 목록과 Batch 준비표에서 실제 보호기가 포함된 `Fmoc-AA-OH` 병명으로 표시되며 one-letter/three-letter 재료명은 노출하지 않습니다.
- Linker는 `Fmoc-NH-PEGn-CH2COOH`와 `Fmoc-N-amido-PEGn-acid`처럼 말단 구조가 다른 판매 형태를 구분하며, 선택 가능한 모든 Fmoc 품목은 DB의 MW와 계산 경로에 연결됩니다.
- 이전 프로젝트의 `R`, `D-R`, `dR`, `PEG4`, `Ahx` 같은 저장값은 로드할 때 정식 병명으로 이관됩니다. 서열 입력의 one-letter 표기 자체는 계속 지원합니다.
- 중복된 `Unit defaults → mL per mmol` 입력은 제거했으며, 작업 부피는 `Solvents / Wash`의 Amide/Rink·2-CTC/Trityl factor 또는 molarity basis에서만 계산·저장됩니다.
- 대괄호 chemical/linker/tag/label은 하나의 토큰으로 보존되고, `A-C-D` 같은 서열은 `Ac-`로 오인되지 않습니다.
- Project 항목 전환 시 변경된 결과표만 저장하여 일반 클릭마다 전체 Treeview를 다시 직렬화하지 않습니다.

## 빠른 시작

전체 사용법은 [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md), Windows
소스 빌드는 [Windows 빌드 안내](docs/WINDOWS_BUILD_KO.md)를 참고하십시오.

### 준비 사항

- Windows 10 또는 11
- 64-bit Python 3.11 또는 3.12

### 소스 실행

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

## Windows 빌드

### Portable 프로그램

```bat
BUILD_EXE_ONLY.bat
```

결과:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

### Windows 설치 프로그램

[Inno Setup](https://jrsoftware.org/isinfo.php)을 설치한 뒤 실행합니다.

```bat
BUILD_INSTALLER.bat
```

결과:

```text
installer\output\SPPS_Planner_Setup_V3.0.0.exe
```

## 저장소 구조

```text
SPPS-Planner/
├─ main_launcher.py              # 프로그램 시작 파일
├─ suite_gui/                    # Tkinter 화면과 작업 흐름
│  ├─ modules/                   # Plan, 작업자, 최종 릴리스 흐름
│  ├─ release.py                 # 공식 GUI 진입점
│  ├─ controller.py              # 직접 정의된 V3.0.0 실행 Controller
│  ├─ classic_base.py            # 정적으로 고정한 기존 Classic UI 기반
│  ├─ position_rules.py          # C-term eq/repeat 위치 규칙
│  └─ release_contract.py        # 최종 실행 함수 검사
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, 계산 엔진, DB, Export
│  └─ data/                      # 공정 및 시약 데이터
├─ tests/                        # 기능·계산 회귀 테스트
├─ tools/                        # 릴리스 및 코드 검사 도구
├─ docs/                         # 구조와 데이터 규칙 문서
└─ installer/                    # Inno Setup 설정
```

직접 실행 순서와 모듈별 책임은
[Architecture 문서](docs/ARCHITECTURE.md)에서 확인할 수 있습니다.
번호형 호환 모듈과 legacy controller는 소스 트리에서 제거되었습니다.
릴리스 검사는 런타임 Controller 재바인딩이 0건인지도 확인합니다.

## 자동저장과 Custom DB

Windows 자동저장 기본 위치:

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

저장된 작업을 초기화하려면 프로그램을 종료한 뒤 위 파일을 삭제합니다.

Custom DB 위치:

```text
Project Manager → Show setup → Custom DB
```

AA/Chemical, coupling reagent, catalyst/additive, base, solvent,
cleavage cocktail, resin 및 기타 물질을 관리할 수 있습니다.

## 검증

최종판에는 Plan 생성, Apply Change, 2-CTC loading, 말단 반응, doubling,
반복 반응, 재료 정렬, 펩타이드 항목, 저장 형식, Custom DB 즉시 반영,
실제 합성 결과 기록·ML 연결과 최종 실행 경로를 검사하는 회귀 테스트가
포함되어 있습니다. 합성 위험 규칙, 실제 classifier 확률, assessment
revision/확인 이력, 위험 시트 Workbook 왕복도 함께 검사합니다.

전체 검증을 5회 반복하려면:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py --passes 5
```

최종 프로그램에서 실제 활성화된 경로만 검사하려면:

```bat
python tools\audit_monkey_patches.py --active-release
```

## 버전

이 저장소의 공개 버전은 **SPPS Planner V3.0.0**으로 고정되어 있습니다.
과거 내부 버전명은 검증된 동작과 이전 import 호환을 유지하는 곳에만
남아 있습니다.

## 라이선스

[LICENSE](LICENSE)를 확인하십시오. 사용자 정의 public academic citation
license이며 OSI 승인 오픈소스 라이선스로 표기하지 않습니다.

---

<div align="center">

**SPPS Planner V3.0.0**  
직접 편집하고 추적할 수 있는 실무형 펩타이드 합성 계획.

</div>
