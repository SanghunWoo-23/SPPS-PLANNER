# SPPS Planner V2.0.0 — 상세 사용자 매뉴얼

**언어:** 한국어  
**English manual:** [USER_MANUAL_EN.md](USER_MANUAL_EN.md)  
**프로젝트 소개:** [README_KO.md](../README_KO.md)

---

## 1. 이 매뉴얼의 목적

이 문서는 SPPS Planner V2.0.0을 처음 실행하는 단계부터 재료량을
확인하고 결과를 저장하는 단계까지 설명합니다. SPPS의 기본 원리는
알지만 프로그램 사용법은 익숙하지 않은 사용자도 따라 할 수 있도록
화면에서 해야 할 일을 순서대로 작성했습니다.

SPPS Planner는 **합성 계획과 계산을 돕는 프로그램**입니다. 실험실 SOP,
위험성 평가, 시약 규격서, 숙련된 연구자의 최종 검토를 대신하지
않습니다. 실제 합성 전에는 반드시 서열, 합성 Scale, Resin Loading,
eq, 농도, 용매량, Cleavage 조건을 다시 확인하십시오.

## 2. 프로그램에서 할 수 있는 일

SPPS Planner는 다음 작업을 하나로 연결합니다.

1. 펩타이드 서열과 프로젝트 정보를 입력합니다.
2. Resin, Scale, Loading, 합성 조건을 선택합니다.
3. 수정 가능한 합성 Plan을 생성합니다.
4. Plan의 각 행을 확인하거나 직접 수정합니다.
5. 수정한 Plan을 기준으로 관련 결과를 다시 계산합니다.
6. Materials, Checklist, Total, Cleavage, Project Summary를 확인합니다.
7. 여러 펩타이드를 Batch Manager에서 합산합니다.
8. 결과를 저장하거나 내보냅니다.

가장 중요한 사용 흐름은 아래와 같습니다.

```text
조건 입력 → Generate → Plan 수정 → Apply Change → 결과 확인 → 저장
```

## 3. 먼저 알아야 할 용어

### Project

현재 작업 전체를 뜻합니다. 한 Project 안에 여러 개의 펩타이드 항목을
둘 수 있습니다.

### Peptide item

Project Manager에 들어 있는 개별 펩타이드입니다. 각 항목은 자신의
서열, 합성 조건, Plan, 계산 결과를 가집니다.

### Generate

`Generate`는 현재 입력된 서열과 설정을 이용해 Plan을 새로 만듭니다.
서열, Resin, Scale 또는 기본 합성 조건을 변경했을 때 사용합니다.

다시 Generate하면 기존 Plan에 직접 입력한 수정 내용이 사라질 수
있습니다. Plan의 셀만 수정했다면 `Apply Change`를 사용하십시오.

### Apply Change

`Apply Change`는 현재 화면에 보이는 수정된 Plan을 계산 기준으로
사용합니다. 원래 서열에서 Plan을 다시 만들지 않고 Materials,
Checklist, Total, Batch 및 관련 출력 결과를 갱신합니다.

### 자동저장과 Save Project

자동저장은 현재 세션을 PC에 보존합니다. `Save Project`는 사용자가
의도적으로 프로젝트 기록을 저장하는 기능입니다. 자동저장은 복구에
도움이 되지만 유일한 백업으로 사용하지 않는 것이 좋습니다.

## 4. 설치와 첫 실행

### Windows 설치 버전

1. GitHub Release에서 `SPPS_Planner_Setup_V2.0.0.exe`를 받습니다.
2. 설치 파일을 실행합니다.
3. 화면 안내에 따라 설치합니다.
4. 생성된 바로가기로 SPPS Planner를 실행합니다.

Windows SmartScreen이 표시되면 계속 진행하기 전에 공식 GitHub
Release에서 받은 파일이 맞는지 확인하십시오.

### 소스코드로 실행

준비 사항:

- Windows 10 또는 Windows 11
- 64-bit Python 3.11 또는 3.12

프로젝트 폴더에서 명령 프롬프트를 열고 아래 명령을 순서대로
실행합니다.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

### 첫 실행 확인

메인 화면이 열리면 다음을 확인합니다.

- Project Manager가 보이는지 확인합니다.
- 서열 입력칸이 비어 있거나 이전 작업이 복원되어 있는지 확인합니다.
- Resin, Scale, Loading, Chemistry 설정을 사용할 수 있는지 확인합니다.
- Plan과 결과 탭을 열 수 있는지 확인합니다.

예전 작업이 자동으로 나타난다면 자동저장 세션이 복원된 것입니다.
초기화 방법은 18장을 참고하십시오.

## 5. 권장 작업 순서

계산 누락을 줄이려면 아래 순서를 권장합니다.

1. 펩타이드 항목을 새로 만들거나 선택합니다.
2. Project, Peptide, LOT 정보를 입력합니다.
3. 서열을 입력하고 확인합니다.
4. Resin을 선택하고 Loading을 입력합니다.
5. 합성 Scale을 입력합니다.
6. Chemistry와 세부 조건을 설정합니다.
7. Doubling, 특수 잔기, Cleavage 조건을 설정합니다.
8. `Generate`를 누릅니다.
9. Plan의 모든 행을 확인합니다.
10. 필요한 행을 직접 수정합니다.
11. `Apply Change`를 누릅니다.
12. 모든 결과 탭을 확인합니다.
13. 프로젝트를 저장하거나 결과를 내보냅니다.

## 6. Project Manager 사용법

Project Manager는 한 번에 여러 펩타이드를 관리하는 곳입니다.

### 새 항목 추가

1. Project Manager를 엽니다.
2. 새 항목 추가 기능을 누릅니다.
3. 구분하기 쉬운 펩타이드 이름을 입력합니다.
4. 새 항목을 선택한 뒤 서열을 입력합니다.

같은 이름을 반복하기보다 `Peptide-01`, `Peptide-02` 또는 사내
프로젝트 코드를 사용하는 것이 좋습니다.

### 항목 복제

조건이 비슷한 펩타이드를 만들 때 Duplicate를 사용합니다.

1. 원본 항목을 선택합니다.
2. Duplicate를 누릅니다.
3. 복제된 항목의 이름을 바꿉니다.
4. 서열 또는 조건을 변경합니다.
5. 입력 조건을 변경했다면 `Generate`를 누릅니다.

복제된 항목에 잘못된 LOT, 서열, Scale 또는 수동 수정 Plan이 남아
있지 않은지 반드시 확인하십시오.

### 항목 삭제

1. 삭제할 항목을 선택합니다.
2. 이름과 서열을 다시 확인합니다.
3. Delete를 누릅니다.
4. 확인창이 나오면 삭제를 확인합니다.

저장하지 않은 정보가 삭제될 수 있으므로 중요한 작업은 먼저
저장하거나 출력하십시오.

### 순서 변경

위로/아래로 이동 기능으로 항목 순서를 바꿀 수 있습니다. Batch 또는
출력 기록을 실제 합성 순서대로 정리할 때 유용합니다.

### 다른 항목으로 이동

다른 펩타이드로 이동하기 전에:

1. 현재 입력 중인 셀의 편집을 끝냅니다.
2. Plan을 수정했다면 Apply Change를 누릅니다.
3. 중요한 작업이면 저장합니다.

이동 후에는 항목 이름과 서열이 맞는지 먼저 확인하십시오.

## 7. Project, Peptide, LOT 정보

이 정보는 저장 파일과 출력 결과에 포함될 수 있으므로 같은 규칙으로
입력하는 것이 좋습니다.

- **Project:** 전체 실험, 의뢰 또는 연구명
- **Peptide name:** 현재 펩타이드의 고유 이름
- **LOT:** 원료 또는 생산 LOT 식별자
- **Notes:** 다른 작업자가 Plan을 이해하는 데 필요한 추가 정보

사내 정책에서 허용하지 않는 개인정보나 기밀정보는 파일명에 넣지
마십시오.

## 8. 서열 입력

### 입력하기 전

말단 변형과 특수 물질을 서열 표기에 포함할지, 별도의 설정 기능으로
지정할지 먼저 정합니다. 한 가지 방식을 일관되게 사용하고 생성된
Plan에서 실제 반영 여부를 확인하십시오.

### 입력 순서

1. 올바른 펩타이드 항목을 선택합니다.
2. 서열 입력칸을 클릭합니다.
3. 서열을 입력하거나 붙여넣습니다.
4. 철자, 구분자, 괄호, 잔기 표기를 확인합니다.
5. N-terminus와 C-terminus 설정을 확인합니다.
6. D-amino acid, 비천연 아미노산, Chemical, Modifier, Tag, Label,
   Linker를 확인합니다.
7. 서열이 정확할 때 다음 단계로 이동합니다.

프로그램이 인식하지 못하는 이름은 오류 또는 불완전한 Plan의 원인이
될 수 있습니다. 필요한 물질이 없다면 Custom DB에 추가한 뒤 다시
Generate하십시오.

### 빈 서열

빈 서열은 빈 상태로 유지됩니다. 프로그램이 가짜 예시 펩타이드나
임시 Plan을 자동으로 넣지 않습니다.

## 9. Resin, Scale, Loading

### Resin 선택

실제 사용하려는 C-terminal chemistry와 실험실 원료에 맞는 Resin을
선택합니다. Rink Amide 계열, 2-CTC, preloaded `CTC(합성기)`, Wang,
HMPB, Sieber Amide, PAL, Tentagel, Manual 등이 제공될 수 있습니다.

이름이 비슷하다는 이유만으로 선택하지 말고 다음을 확인하십시오.

- 작용기와 원하는 C-terminus
- 실제 제조사 규격
- Resin Loading
- Preloaded 또는 unloaded 여부
- Swelling과 cleavage 조건

### Loading

화면에 표시된 단위에 맞춰 Loading을 입력합니다. 실제 Resin의
성적서 또는 승인된 내부 기록의 값을 사용하십시오.

Loading을 잘못 입력하면 Resin 양과 관련 시약 계산 전체가 달라집니다.

### Scale

화면에 표시된 단위에 맞춰 합성 Scale을 입력합니다. 목표 정제 수율이나
최종 제품 질량을 잘못 입력하지 않도록 주의하십시오.

### 2-CTC 주의사항

`2-CTC` 직접 Loading은 전용 Loading chemistry를 사용합니다. Loading
AA와 DIEA 조건을 확인하십시오. Apply Change 후 이 행이 일반적인
DIC/HOBt coupling 행으로 바뀌지 않았는지 확인해야 합니다.

과거 저장값 `CTC(합성용)`은 `CTC(합성기)`로 호환됩니다.

## 10. Chemistry와 세부 설정

다음 위치를 엽니다.

```text
Project Manager → Show setup
```

선택한 합성 방식에 따라 세부 항목은 달라질 수 있습니다. 화면에
나타나는 다음 값을 모두 확인하십시오.

- Coupling reagent
- Catalyst 또는 additive
- Base
- Solvent
- Amino-acid eq
- Coupling-reagent eq
- Repeat 횟수
- Deprotection 조건
- Wash 조건
- Doubling 위치
- Cleavage cocktail

Preset 버튼은 합성 조건을 바꿉니다. 버튼을 누르는 것만으로 Plan이
항상 생성되는 것은 아닙니다. Preset 선택 후 값을 확인하고, 새 Plan이
필요하면 `Generate`를 누르십시오.

## 11. Doubling과 반복 반응

특정 위치에서 Coupling을 반복해야 할 때 위치별 Doubling을 사용합니다.

1. Doubling 설정을 엽니다.
2. 반복할 잔기 위치를 선택하거나 입력합니다.
3. 위치 번호가 화면 서열의 어느 방향을 기준으로 하는지 확인합니다.
4. Plan을 Generate합니다.
5. 대상 Coupling 행의 Repeat 값이 맞는지 확인합니다.
6. Apply Change 후 Materials와 Checklist를 확인합니다.

Repeat는 반드시 2회로 제한되지 않습니다. 2보다 큰 값을 사용했다면
Plan, 재료 합계, Checklist에 같은 횟수가 반영됐는지 확인하십시오.

## 12. 합성 Plan 생성

Generate를 누르기 전에 다음을 확인합니다.

- 올바른 펩타이드 항목
- 올바른 서열
- 말단과 Modification
- Resin
- Loading
- Scale
- Chemistry
- Doubling 위치
- Cleavage 설정

그다음:

1. `Generate`를 누릅니다.
2. Plan이 나타날 때까지 기다립니다.
3. 첫 행부터 마지막 행까지 읽습니다.
4. Loading, Coupling, Deprotection, Wash, 말단 변형, 최종 작업을
   확인합니다.
5. 오류창이 없었다는 이유만으로 바로 실험에 사용하지 마십시오.

## 13. Plan 확인과 직접 수정

Plan은 수정 가능한 공정 표입니다. 행 종류에 따라 Operation, Material,
Unit, MW, Density, eq, Reagent, Solvent, Repeat 등의 열이 표시될 수
있습니다.

### 셀 수정

1. 수정할 셀을 정확히 선택합니다.
2. 새 값을 입력합니다.
3. Unit을 확인합니다.
4. 필요한 경우 MW와 Density를 확인합니다.
5. eq와 Repeat를 확인합니다.
6. 관련 Reagent와 Solvent를 확인합니다.
7. 셀 편집을 완료합니다.
8. `Apply Change`를 누릅니다.

### 물질 교체

물질을 교체할 때 이름만 바꾸고 끝내면 안 될 수 있습니다. MW, Density,
Unit, eq도 함께 바뀌어야 하는지 확인하십시오.

예를 들어 `Ac2O` 행을 `Ac-Glu(OtBu)-OH`로 교체하면 화학적 의미가
달라집니다. 교체 후 Materials, Checklist, Total, Batch, Export가 새
행을 기준으로 계산되는지 확인하십시오.

### 행 삭제

1. 삭제할 행을 선택합니다.
2. `Delete selected row`를 누릅니다.
3. 의도한 행 하나만 삭제됐는지 확인합니다.
4. `Apply Change`를 누릅니다.
5. 연결된 결과를 다시 확인합니다.

### Generate와 Apply Change 선택

| 상황 | 누를 버튼 |
| --- | --- |
| 서열을 변경함 | `Generate` |
| Resin, Scale, 기본 Chemistry를 변경함 | `Generate` |
| Plan 셀을 직접 수정함 | `Apply Change` |
| Plan 행을 교체하거나 삭제함 | `Apply Change` |
| 수동 수정을 버리고 입력값에서 다시 만들고 싶음 | `Generate` |

## 14. 결과 탭 확인

### Materials

선택한 펩타이드에 필요한 계산 재료를 보여줍니다. 다음을 확인합니다.

- Resin
- Amino acid와 Modification
- Coupling reagent
- Catalyst/additive
- Base
- Solvent
- Cleavage component
- Unit와 수량

### Selected Total Materials

선택된 범위의 재료를 합산합니다. 어떤 항목이 선택되어 있는지와 합계
범위가 의도와 맞는지 확인하십시오.

### Checklist

Plan을 작업 순서에 맞게 확인하기 위한 목록입니다. Plan을 직접
수정하거나 행을 삭제하거나 Repeat를 바꿨다면 Checklist와 Plan이
서로 같은지 비교하십시오.

### Cleavage Cocktail

선택한 Preset 또는 Custom cocktail, 전체량, 각 성분 비율, 질량/부피
표시를 확인합니다. 화학적 적합성과 실험 안전성은 별도로 검토해야
합니다.

### Project Summary

최종 요약 화면입니다. 선택한 펩타이드, Scale, Resin, Plan 및 재료
계산과 일치하는지 확인하십시오.

## 15. Batch Manager

여러 펩타이드 항목의 재료량을 합산할 때 사용합니다.

1. 모든 펩타이드의 수정 작업을 완료하고 Apply Change를 누릅니다.
2. Batch Manager를 엽니다.
3. 포함할 펩타이드 항목을 선택합니다.
4. 각 항목의 이름, Scale, 상태를 확인합니다.
5. Batch를 다시 계산합니다.
6. 펩타이드별 결과를 확인합니다.
7. Batch 전체 합계를 확인합니다.
8. 중복 항목이나 빠진 항목이 없는지 확인한 후 출력합니다.

나중에 개별 펩타이드 Plan을 변경했다면 Batch Manager로 돌아가 다시
계산해야 합니다.

## 16. Custom DB

다음 위치에서 엽니다.

```text
Project Manager → Show setup → Custom DB
```

관리 가능한 분류:

- AA/Chemical
- Coupling reagent
- Catalyst/additive
- Base
- Solvent
- Cleavage cocktail component
- Resin
- Other material

### 새 물질 추가

1. 정확한 분류를 선택합니다.
2. 중복되지 않고 일관된 이름을 입력합니다.
3. MW를 입력합니다.
4. 부피 계산에 필요한 경우 Density를 입력합니다.
5. 필요한 메모를 입력합니다.
6. 저장합니다.
7. 원하는 선택 목록에 나타나는지 확인합니다.

### 수정 또는 삭제

수정하기 전에 기존 프로젝트가 해당 값을 사용하는지 확인하십시오.
삭제 전에 중요한 프로젝트를 저장하십시오. DB 값을 바꾸면 이후
계산 결과도 달라질 수 있습니다.

## 17. 저장과 출력

### Save Project

다음 시점에 저장하는 것이 좋습니다.

- 초기 조건 입력 완료 후
- Plan 생성 및 검토 후
- Plan 직접 수정 후
- Batch 계산 전
- 프로그램 종료 전

### Export

작업 흐름에 따라 CSV, XLSX 또는 JSON 출력이 제공될 수 있습니다.

출력 전:

1. 모든 Plan 수정에 Apply Change를 적용합니다.
2. 선택된 펩타이드 또는 Batch를 확인합니다.
3. Project, Peptide, LOT 정보를 확인합니다.
4. 합계와 단위를 확인합니다.
5. 알아보기 쉬운 파일명과 저장 위치를 선택합니다.
6. 출력 파일을 직접 열어 일부 내용을 확인합니다.

## 18. 자동저장과 초기화

Windows의 기본 자동저장 위치:

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

자동으로 복원되는 작업을 초기화하려면:

1. 중요한 내용을 먼저 저장하거나 출력합니다.
2. SPPS Planner를 종료합니다.
3. 파일 탐색기에서 위 경로를 엽니다.
4. 나중에 복구할 수 있도록 필요하면 파일을 백업합니다.
5. 세션 파일을 제거합니다.
6. SPPS Planner를 다시 실행합니다.

구조를 정확히 알지 못한다면 자동저장 JSON을 직접 편집하지 마십시오.

## 19. 실제 합성 전 최종 점검표

- [ ] 올바른 Project와 Peptide item
- [ ] 서열과 잔기 순서
- [ ] N-terminus와 C-terminus
- [ ] D/비천연 잔기, Tag, Label, Linker
- [ ] Resin 종류와 preloaded/unloaded 상태
- [ ] Resin Loading과 합성 Scale
- [ ] Coupling chemistry와 eq
- [ ] Deprotection과 Wash 조건
- [ ] Doubling 위치와 Repeat 값
- [ ] 말단 Modification
- [ ] Cleavage cocktail
- [ ] Plan의 모든 행 검토
- [ ] 수동 수정 후 Apply Change 실행
- [ ] Materials와 Checklist가 Plan과 일치
- [ ] Total과 Batch의 합산 범위
- [ ] 출력 파일을 직접 열어 확인
- [ ] 실험실 SOP에 따른 최종 검토

## 20. 문제 해결

### Plan이 바뀌지 않음

- 올바른 펩타이드 항목을 선택했는지 확인합니다.
- 입력 조건을 바꿨다면 `Generate`를 누릅니다.
- Plan 셀을 바꿨다면 편집을 끝내고 `Apply Change`를 누릅니다.

### 직접 수정한 내용이 사라짐

`Generate`는 입력 조건에서 Plan을 다시 만듭니다. 필요한 수정을 다시
입력하고 이후에는 `Apply Change`를 사용하십시오.

### 필요한 물질이 없음

철자와 표기를 확인합니다. Custom DB에 올바른 값을 추가한 뒤 다시
Generate합니다.

### 합계가 이전 값으로 보임

현재 셀 편집을 끝내고 `Apply Change`를 누릅니다. Batch Manager를
사용 중이면 Batch도 다시 계산합니다.

### 예전 프로젝트가 자동으로 열림

자동저장 세션이 복원된 것입니다. 18장의 초기화 방법을 따르십시오.

### 프로그램이 실행되지 않음

소스로 실행한다면 Python 버전, 가상환경 활성화, requirements 설치,
프로젝트 폴더에서 `main_launcher.py`를 실행했는지 확인합니다.

## 21. 데이터와 안전 관련 제한

- 계산 결과의 정확도는 입력값에 따라 달라집니다.
- Custom DB 값은 사용자가 검증해야 합니다.
- 제조사별 Loading과 Density가 다를 수 있습니다.
- 특수 잔기는 별도의 공정 검증이 필요할 수 있습니다.
- 합성 및 Cleavage 조건은 실험실 SOP와 비교해야 합니다.
- 중요한 프로젝트와 출력 파일은 별도로 백업하십시오.

## 22. 빠른 참고표

```text
새 서열 또는 기본 설정 변경 → Generate
Plan 직접 수정               → Apply Change
여러 펩타이드 관리           → Project Manager / Batch Manager
새 물질 추가                 → Show setup / Custom DB
예전 세션 자동 복원          → 자동저장 파일 초기화
실제 실험 전                 → Plan, Materials, Checklist, Total, Export 확인
```

