# SPPS Planner V3.0.0 Windows 빌드

## 자동 설치와 전체 빌드

압축을 완전히 해제한 뒤 다음 파일을 실행한다.

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

이 스크립트는 Python 3.11/3.12와 Inno Setup을 확인하고, 없으면 Windows
Package Manager(`winget`)로 현재 사용자 범위에 설치한다. 이어서 Python
의존성, V3 release contract, PyInstaller EXE, Inno Setup Installer를 순서대로
만든다. 관리자 권한 설치를 요구하지 않는다.

최종 결과:

```text
dist\SPPS_Planner\SPPS_Planner.exe
installer\output\SPPS_Planner_Setup_V3.0.0.exe
```

## 개별 빌드

```bat
BUILD_EXE_ONLY.bat
BUILD_INSTALLER.bat
```

CI나 자동화에서는 두 스크립트에 `--no-pause`를 전달할 수 있다. 빌드는
V3.0.0 내부 version, EXE version resource, Installer metadata, 삭제된 legacy
import 부재와 생성된 PE 파일의 `MZ` header를 검사한다.

## 실제 Windows 최종 확인

1. Windows 10/11 64-bit에서 Installer 실행 및 일반 사용자 경로 설치
2. 시작 메뉴/바탕화면 shortcut 실행
3. 빈 Work Item startup, V3.0.0 title/icon 확인
4. Generate → Plan 편집 → Apply Change → Export 확인
5. Work Item 독립 창과 모든 5개 업무 탭 확인
6. Project Save/Load/Save As, `.bak` 복구, Data Workbook 왕복 확인
7. 한글 경로와 공백 포함 경로에서 HPLC data/method link 확인
8. 종료 후 재실행, 제거 프로그램 실행 확인

Windows에서 생성한 EXE/Installer 자체는 다른 OS에서 교차 빌드한 파일로
대체하지 않는다. 최종 배포물은 위 체크를 실제 Windows에서 통과한 파일을
사용한다.
빌드가 끝나면 `BUILD_EXE_ONLY.bat`가 생성된 EXE 자체를 `--self-test`로
실행합니다. 이 검사는 V3.0.0 모듈, Fmoc 보호 아미노산, Batch 계산,
chemical/linker/tag/label 파싱이 실제 패키지 안에서도 동작하는지 확인하며,
하나라도 실패하면 빌드를 실패로 종료합니다.
