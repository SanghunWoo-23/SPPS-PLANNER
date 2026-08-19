<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="150">

# SPPS Planner V4.0.0

**고체상 펩타이드 합성(SPPS) 계획용 데스크톱 소프트웨어**

시퀀스 파싱 · 편집 가능한 합성 Plan · Materials · Checklist · Batch · 실험 데이터 기반 추천

[![Release](https://img.shields.io/badge/release-V4.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)

**[English](README.md) · [사용자 매뉴얼](docs/USER_MANUAL_KO.md) · [Architecture](docs/ARCHITECTURE.md) · [Windows 빌드](docs/WINDOWS_BUILD_KO.md)**

</div>

---

## 개요

SPPS Planner는 펩타이드 설계와 합성 조건을 바탕으로 수정 가능한 합성 작업 흐름을 생성합니다. 생성된 Plan은 직접 편집할 수 있으며, **Apply Change**는 원래 시퀀스를 몰래 다시 생성하지 않고 화면에 보이는 Plan을 기준으로 Materials, Checklist, Total Materials 등을 다시 계산합니다.

V4.0.0에는 Loading, Coupling, Cleavage 실험 결과를 로컬에 기록하는 Experimental Data 계층도 포함됩니다. 추천은 반복된 과거 조건을 우선하며, 검토된 데이터가 부족한 경우 임의로 정밀한 조건을 만들어내지 않습니다. Public/GitHub 버전에는 사내·개인 실험 이력이 포함되지 않습니다.

```text
Sequence / modifier / branch 설정
                ↓
Resin · scale · loading · coupling chemistry
                ↓
           Generate
                ↓
Plan · Materials · Checklist · Total Materials
                ↓
           Plan 직접 수정
                ↓
          Apply Change
```

## 주요 기능

- **Sequence 처리** — 말단기, D/non-natural residue, chemical, linker, label, tag 및 실제 보호기 포함 bottle-level building block 인식.
- **Resin & Loading** — Rink Amide 계열, 2-CTC direct loading, Wang, HMPB, Sieber Amide, PAL, Tentagel, Manual profile.
- **편집 가능한 합성 Plan** — coupling, deprotection, wash, loading, terminal modification, repeat, doubling.
- **Materials / Checklist / Totals** — 현재 Plan과 연결된 계산 결과.
- **Cleavage** — preset 및 custom cocktail, 성분별 mass/volume 처리.
- **Branch 지원** — branched synthesis 설정과 orthogonal protecting-group 흐름.
- **Project / Batch 관리** — 여러 peptide item, 상태 저장, batch 계산, export.
- **Custom DB** — AA, chemical, reagent, catalyst/additive, base, solvent, resin 등 사용자 재료 추가.
- **Experimental Data** — Loading, Coupling, Cleavage 결과 기록 및 import.
- **Recommend** — 동일·반복 historical consensus를 가장 먼저 사용하고, 근거가 있을 때만 제한적인 데이터 기반/chemistry-rule 추천.
- **Windows 빌드** — PyInstaller portable EXE, packaged runtime self-test, Inno Setup installer.

## Public 데이터 정책

이 GitHub 배포본은 **data-sanitized public build**입니다. Experimental Data schema, 기록/import UI, recommendation engine, 빈 runtime template은 포함하지만 회사/개인 실험 이력과 private product-to-sequence mapping은 포함하지 않습니다.

사용자가 생성한 데이터는 저장소 밖 Public 전용 사용자 폴더에 저장됩니다. 자세한 내용은 [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)를 확인하십시오.

## 빠른 시작

### 요구 사항

- Windows 10 또는 11
- 64-bit Python 3.11 또는 3.12

### 소스에서 실행

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

## Windows 빌드

### Portable EXE

```bat
BUILD_EXE_ONLY.bat
```

예상 결과:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

### Installer

Inno Setup 설치 후:

```bat
BUILD_INSTALLER.bat
```

의존성 확인/설치부터 한 번에 진행하려면:

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

예상 결과:

```text
installer\output\SPPS_Planner_Setup_V4.0.0.exe
```

빌드 스크립트는 source validation, PyInstaller 생성, packaged runtime self-test, installer validation을 구분하여 어느 단계에서 문제가 발생했는지 확인할 수 있게 구성되어 있습니다.

## 저장소 구조

```text
SPPS-Planner/
├─ main_launcher.py              # 데스크톱 진입점
├─ suite_gui/                    # Tkinter UI 및 workflow controller
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, 계산 engine, database, export
│  └─ data/                      # 공개 가능한 시약/공정 기본값 및 빈 template
├─ tests/                        # 회귀 및 동작 contract 테스트
├─ tools/                        # release/build/source audit 도구
├─ docs/                         # 사용자·구조·parser·데이터 문서
├─ installer/                    # Inno Setup 설정
├─ requirements.txt
└─ requirements-dev.txt
```

## Runtime 데이터

Public build의 사용자 생성 데이터는 저장소 밖에 저장됩니다. Windows의 core 데이터 폴더는 다음을 기준으로 합니다.

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

Session, Experimental DB, import한 lab data, model, log, output 등은 Git에 commit하지 않는 것을 전제로 합니다.

## 검증

개발 의존성을 설치한 뒤 release 검증을 실행할 수 있습니다.

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
python tools\verify_windows_release.py
```

최종 active release의 runtime rebinding 감사:

```bat
python tools\audit_monkey_patches.py --active-release
```

테스트는 sequence/parser, Generate/Apply Change, loading, coupling, cleavage, doubling/repeat, Materials/Checklist/Total Materials, persistence, Experimental Data, recommendation safety, Windows release contract를 포함합니다.

## 문서

- [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md)
- [English user manual](docs/USER_MANUAL_EN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Parser contract](docs/SPPS_PARSER_CONTRACT.md)
- [Reagent database schema](docs/SPPS_REAGENT_DATABASE_SCHEMA.md)
- [Experimental Data / ML 가이드](docs/V4_EXPERIMENTAL_ML_KO.md)
- [Windows 빌드 가이드](docs/WINDOWS_BUILD_KO.md)
- [Public data policy](PUBLIC_DATA_POLICY.md)

## 버전

현재 Public release: **V4.0.0**.

## 라이선스

[LICENSE](LICENSE)를 확인하십시오. 현재 저장소는 포함된 custom public academic citation license를 사용합니다. 라이선스가 변경되지 않는 한 OSI 승인 오픈소스 라이선스로 표현하지 않습니다.
