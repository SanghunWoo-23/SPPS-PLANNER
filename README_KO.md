<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner 아이콘" width="150">

# SPPS Planner

### 펩타이드 서열을 편집 가능한 합성 계획과 작업 기록으로

**고체상 펩타이드 합성(SPPS)** 계획, 재료량 계산, 다중 펩타이드 관리,
작업자용 기록 출력을 하나로 연결한 데스크톱 프로그램입니다.

[![Release](https://img.shields.io/badge/release-V2.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)
[![Tests](https://img.shields.io/badge/regression_tests-61%20passed-16A34A?style=for-the-badge)](#검증)

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

| 영역 | 기능 |
| --- | --- |
| **Project Manager** | 여러 펩타이드 관리, 복제·삭제·순서 이동, 펩타이드별 입력값과 계산 결과 보존 |
| **Sequence 해석** | 말단기, 일반·D형·비천연 아미노산, chemical, modifier, tag, label, linker 인식 |
| **Resin 및 Loading** | Rink Amide 계열, 2-CTC 직접 loading, preloaded `CTC(합성기)`, Wang, HMPB, Sieber Amide, PAL, Tentagel, Manual |
| **합성 Plan** | Coupling·deprotection·wash 단계 생성 및 물질명, MW, 밀도, eq, 시약, 용매, 반복 횟수 직접 편집 |
| **Apply Change** | 수정한 Plan을 서열에서 다시 만들지 않고 현재 보이는 Plan 기준으로 연관 결과 재계산 |
| **Materials** | Resin, 아미노산, coupling reagent, catalyst, base, solvent, modifier, cleavage component 계산 |
| **Doubling 및 반복** | 위치별 doubling과 2회 이상의 반복 반응을 Materials와 Checklist까지 동기화 |
| **Cleavage** | Preset 및 사용자 cocktail 조성, 액체·고체 성분의 질량/부피 표시 |
| **Batch Manager** | 여러 프로젝트의 펩타이드별·전체 Batch 재료량 통합 계산 |
| **저장 및 출력** | 자동저장과 CSV/XLSX/JSON 출력, Project·Peptide·LOT 정보 기록 |
| **Custom DB** | 사용자 물질의 분류, MW, 밀도, 메모 추가·수정·삭제 |

## 작업자 중심 동작

- **Generate**는 현재 입력값에서 Plan을 새로 생성합니다.
- **Apply Change**는 직접 수정한 Plan을 보존하고 연결된 결과를 갱신합니다.
- 빈 서열에 가짜 펩타이드나 예시 Plan을 넣지 않습니다.
- Chemistry preset 버튼은 조건만 변경하고 Plan을 멋대로 생성하지 않습니다.
- `2-CTC` 직접-loading 행은 일반 DIC/HOBt coupling으로 잘못 변환하지 않습니다.
- 과거 저장값 `CTC(합성용)`은 `CTC(합성기)`로 호환됩니다.

## 빠른 시작

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
installer\output\SPPS_Planner_Setup_V2.0.0.exe
```

## 저장소 구조

```text
SPPS-Planner/
├─ main_launcher.py              # 프로그램 시작 파일
├─ suite_gui/                    # Tkinter 화면과 작업 흐름
│  ├─ modules/                   # Plan, 작업자, 최종 릴리스 흐름
│  ├─ release.py                 # 공식 GUI 진입점
│  ├─ release_composition.py     # 적용 순서
│  └─ release_contract.py        # 최종 실행 함수 검사
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, 계산 엔진, DB, Export
│  └─ data/                      # 공정 및 시약 데이터
├─ tests/                        # 기능·계산 회귀 테스트
├─ tools/                        # 릴리스 및 코드 검사 도구
├─ docs/                         # 구조와 데이터 규칙 문서
└─ installer/                    # Inno Setup 설정
```

실행 순서와 호환 코드·활성 코드의 구분은
[Architecture 문서](docs/ARCHITECTURE.md)에서 확인할 수 있습니다.

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
반복 반응, 재료 정렬, 펩타이드 항목, 저장 형식과 최종 실행 경로를
검사하는 회귀 테스트가 포함되어 있습니다.

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

이 저장소의 공개 버전은 **SPPS Planner V2.0.0**으로 고정되어 있습니다.
과거 내부 버전명은 검증된 동작과 이전 import 호환을 유지하는 곳에만
남아 있습니다.

## 라이선스

[LICENSE](LICENSE)를 확인하십시오. 사용자 정의 public academic citation
license이며 OSI 승인 오픈소스 라이선스로 표기하지 않습니다.

---

<div align="center">

**SPPS Planner V2.0.0**  
직접 편집하고 추적할 수 있는 실무형 펩타이드 합성 계획.

</div>
