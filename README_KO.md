<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner v7.0.0

**고체상 펩타이드 합성(SPPS) 계획·계산·기록을 지원하는 Windows 중심 데스크톱 프로그램**

[![Release](https://img.shields.io/badge/release-v7.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#빠른-시작)

[English](README.md) · [사용자 매뉴얼](docs/USER_MANUAL_KO.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)

</div>

## 소개

SPPS Planner는 peptide synthesis setup을 입력하면 합성 Plan, Materials, Checklist, Batch 계산과 관련 기록을 연결해 주는 데스크톱 도구입니다.

V7의 기본 흐름은 다음과 같습니다.

```text
Project Manager
  → Add / Edit peptide
  → Sequence / Scale / Resin / Loading / exact bottle 설정
  → Generate
  → Plan / Materials / Checklist / Cleavage 검토
  → Batch Manager / Export
```

## V7 주요 기능

- **Project Manager 중심 Add/Edit workflow**
- Sequence, Scale, Copies, Resin, Loading, LOT를 한 화면에서 설정
- Coupling reagent / Additive / Base / Solvent를 **exact bottle identity**로 관리
- **My recipes** 저장 / 불러오기 / Rename / Delete / Favorite / Backup / Import
- 최근 사용 recipe와 bottle을 빠르게 재사용
- STEP 3에서 저장 전 setup 검토 및 변경사항 확인
- synthesis-defining edit 시 해당 peptide의 오래된 계산 결과만 무효화
- Project Manager에서 Ready / Calculated / Error 상태 확인
- Batch Manager solution-prep defaults와 peptide-specific recipe 분리
- Loading / Cleavage recommendation과 실험 기록 지원
- Public build는 Private 실험 이력, 회사 로컬 DB, 원본 실험 사진을 포함하지 않음

## 빠른 시작

### 권장 환경

- Windows 10 / 11
- Python 3.11 또는 3.12 (64-bit)

### 소스에서 실행

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### 개발 / 검증

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

Windows 패키징은 [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md)를 참고하십시오.

## 기본 사용법

1. **Project Manager → Add**를 선택합니다.
2. Sequence, Scale, Resin, Loading 등 peptide 조건을 입력합니다.
3. Reagent / Additive / Base / Solvent를 선택합니다.
4. STEP 3에서 setup을 검토한 뒤 저장합니다.
5. **Generate**로 Plan을 생성합니다.
6. 필요하면 Plan을 수정하고 **Apply Change**로 연결 계산을 갱신합니다.
7. Materials / Checklist / Cleavage / Batch 정보를 확인합니다.

자세한 사용법은 [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md)을 참고하십시오.

## 중요한 chemistry identity 예시

- `NMM` = N-Methylmorpholine, **Base**
- `NMP` = N-methyl-2-pyrrolidone, **Solvent**
- `HOBt (anhydrous)`와 `HOBt hydrate / monohydrate`는 별도 bottle identity로 취급

## 공개 데이터 정책

Public repository에는 회사 내부 실험 history/seed, 원본 실험 사진, 로컬 SQLite DB, confidential sample 정보가 포함되지 않습니다.

자세한 내용은 [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)를 참고하십시오.

## 문서

| 문서 | 내용 |
| --- | --- |
| [사용자 매뉴얼](docs/USER_MANUAL_KO.md) | 상세 사용법 |
| [English User Manual](docs/USER_MANUAL_EN.md) | English manual |
| [Architecture](docs/ARCHITECTURE.md) | 코드 구조 및 주요 컴포넌트 |
| [Reagent DB Schema](docs/SPPS_REAGENT_DATABASE_SCHEMA.md) | Reagent database schema |
| [Parser Contract](docs/SPPS_PARSER_CONTRACT.md) | Sequence parser contract |
| [Windows Build](docs/WINDOWS_BUILD_KO.md) | Windows EXE / installer build |
| [Release Notes](RELEASE_NOTES_V7.0.0_FINAL.md) | v7.0.0 릴리스 요약 |

## 개발 원칙

- Public / Private 계보 분리
- runtime monkey patch / placeholder / dummy production implementation 금지
- 계산 결과와 실험 근거의 출처를 가능한 한 명확히 구분
- 기존 검증된 chemistry behavior를 UI 변경 때문에 우발적으로 변경하지 않음

## License

라이선스 조건은 [LICENSE](LICENSE)를 확인하십시오.
