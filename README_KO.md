# SPPS Planner V2.0.0

고정된 Classic 작업 흐름을 기반으로 하는 SPPS 계획 데스크톱 프로그램의 **V2.0.0 완성형 GitHub 소스 저장소**입니다. 실행 소스, 빌드 스크립트, 필수 데이터와 회귀 테스트를 포함하며 프로그램 버전은 **V2.0.0으로 고정**되어 있습니다.

## 주요 기능

- SPPS Project/Batch 계획
- Plan 직접 편집 및 Apply Change 동기화
- `Ac2O` 행을 `Ac-Glu(OtBu)-OH`로 변경한 뒤 Apply Change 시 현재 Plan 기준으로 Materials, Checklist, Total, Batch, Export 재계산
- 아미노산 eq와 위치별 doubling 제어
- Resin, 용매, 염기, 촉매, 아미노산/chemical, cleavage 재료 계산
- Sequence의 chemical/modifier 인식
- CSV/XLSX Export 및 LOT 정보
- `CTC(합성기)`에서 입력 Sequence 전체 coupling, loading AA/DIEA 미생성
- 과거 저장값의 `CTC(합성용)`은 `CTC(합성기)`로 변환하되 Resin 선택지에는 표시하지 않음
- Custom DB에서 AA/Chemical, coupling reagent, catalyst/additive, base, solvent 등을 추가·수정·삭제
- `Use DIC/HOBt`, `Use HBTU/NMP 10eq` 버튼은 chemistry/default 조건만 전환하며 Plan 프리셋 행을 자동 생성하지 않음

## 소스 실행

Windows와 Python 3.11 또는 3.12를 권장합니다.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

## Windows EXE 생성

```bat
BUILD_EXE_ONLY.bat
```

결과:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

## Windows Installer 생성

Inno Setup 6 또는 7 설치 후 실행합니다.

```bat
BUILD_INSTALLER.bat
```

결과:

```text
installer\output\SPPS_Planner_Setup_V2.0.0.exe
```

## 이전 peptide items가 표시되는 경우

프로그램은 Windows 자동 저장 파일에서 이전 peptide items를 복원할 수 있습니다.

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

초기화하려면 프로그램을 종료한 뒤 위 파일을 삭제합니다. 자동 저장 파일과 사용자 출력물은 `.gitignore`에 의해 GitHub 커밋 대상에서 제외됩니다.

## Custom DB 사용

`Project Manager`에서 **Show setup**을 누른 뒤 `Custom DB` 탭을 엽니다.

추가 가능한 분류:

- AA/Chemical
- Coupling reagent
- Catalyst/additive
- Base
- Solvent
- Cleavage cocktail
- Resin
- Other

이름, MW, Density, Note를 입력하고 `Add / Update material`을 누르면 기존 Plan 편집 목록과 계산용 MW/Density lookup에 즉시 반영됩니다. 선택 후 `Delete selected material`로 삭제할 수 있습니다. 사용자 항목은 기존 peptide item과 함께 자동 저장 세션에 보존됩니다.

```text
%USERPROFILE%\.spps_planner\spps_planner_session_v1.json
```

## 저장소 구조

- `main_launcher.py`: 실행 진입점
- `suite_gui/`: Classic UI와 작업 흐름
- `apps/spps_planner_app/spps_planner/`: parser, 계산 엔진, DB, Export
- `apps/spps_planner_app/data/`: 시약 및 공정 데이터
- `tests/`: 회귀 테스트
- `installer/`: Inno Setup 설정
- `docs/`: Parser contract 및 reagent database schema 문서

## 테스트

```bat
python -m pip install -r requirements-dev.txt
set PYTHONPATH=%CD%\apps\spps_planner_app;%CD%
python -m pytest -q tests\test_spps_normalized_logic.py tests\test_v200_final_release.py tests\test_v200_custom_db_tab_restore.py tests\test_v200_apply_change_terminal_sync.py tests\test_v200_2ctc_apply_loading_preserve.py tests\test_v200_preset_buttons_no_autogenerate.py -k "not gui"
```

## 라이선스

[`LICENSE`](LICENSE)를 확인하십시오. 사용자 정의 academic citation license이며 OSI 승인 오픈소스 라이선스로 표기하지 않습니다.
