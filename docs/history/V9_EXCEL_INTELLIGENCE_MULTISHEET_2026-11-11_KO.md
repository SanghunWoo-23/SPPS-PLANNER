# SPPS Planner V9.0.0 — Excel Intelligence 다중 시트 가져오기

## 변경 목적

기존 V9.0.0의 파일별 검토·다중 파일 병합·원자적 저장 기능을 보존하면서, 한 통합문서의 여러 실험 시트를 자동 발견하고 **시트별로 승인**해 저장하도록 확장하였다. UI는 비동기 작업 큐를 사용하므로 스캔 중 대화창을 차단하지 않는다.

## 사용 방법

1. AI / Excel Assistant를 연다.
2. `Automatically queue data worksheets...`를 켜고 `Choose Excel(s) / CSV(s)`를 클릭해 여러 파일을 선택한다.
3. 프로그램이 각 Excel의 헤더 12행을 검사하여 `Sequence + 실측 수득률/순도/과정별 결과` 또는 `Sequence + Run ID/스케일/반응 메타데이터`를 식별한다. GUIDE·README·숨긴 탭은 자동 큐에서 제외한다.
4. **각 탭마다** `Check & clean` → 컬럼·단위·실측값 검토 → 승인 체크 → `Stage reviewed file / Next`를 수행한다. 데이터가 아닌 탭은 `Skip worksheet`로 건너뛴다.
5. 승인한 탭을 `Save combined data`로 Append/Replace 저장한다. 이전 파일은 버전별 백업되며, 저장 이후 모델 재학습 여부를 별도로 선택한다.
6. 필요하면 `Audit data quality`로 Run ID 충돌·중복·품질을 검사한다.

## 지원 입력·제한

- **.xlsx / .xlsm / .csv / .tsv / .txt** 지원. Excel 매크로는 실행하지 않는다. 구형 `.xls`는 `.xlsx`로 변환해야 한다.
- 기본 최대 32개 파일/배치, 96개 자동 큐 시트, 한 통합문서 64개 시트, 각 파일 12 MB, 전체 최대 20,000행.
- 기존 `GUIDE` 및 미인식 시트의 검토는 사용자 수동 선택으로 가능하다.
- 수식은 계산하지 않는다. Excel에서 재계산 결과가 저장되지 않은 수식 셀은 결측으로 취급하고 미리보기 경고로 알려준다.
- Excel 숫자 서식 `0.75 → 75%` 변환은 기존 명시적 체크박스로 제어한다. 수득률과 순도는 실측으로 확인해야 한다.
- 데이터는 ChatGPT 라이브러리가 아닌 SPPS Planner의 사용자 로컬 프로필에 저장된다. 사용자 데이터의 외부 전송과 SOP 자동 적용은 수행하지 않는다.
- AI 학습은 실험 데이터의 독립적 검증을 대체하지 않는다.

## 명령행 사전 감사 (저장하지 않음)

```bash
python tools/excel_intake_audit_v9.py data.xlsx additional.csv
```

JSON 결과에는 각 시트의 출처 파일명, 시트명, 감지된 컬럼명 및 행 수와 누락 경고만 기록한다. 펩타이드 서열이나 측정값의 원문은 출력하지 않는다. `--first-sheet` 옵션으로 통합문서당 한 탭씩만 검사할 수 있다.

## 검증 기준

- 단일/다중 파일·시트, GUIDE/숨김 시트, 수식 경고, `.xlsm`, 12행까지 헤더, 변경된 입력 거부, CLI 미리보기 비변경성.
- 실제 가상 Tk GUI에서 2개 시트를 각각 승인해 통합 저장하고, 저장된 레코드 2행과 출처 시트 이름을 비교한다.
- 새 기능은 `suite_gui/ai_excel_core_v9.py`, `suite_gui/ai_excel_dialog_v9.py`, `tools/excel_intake_audit_v9.py`에 일반 함수로 구현. 런타임 monkey patch 없음.
- 이전 화학 엔진 및 Project/Generate/Apply 경로는 그대로 유지.

## 포함된 빈 실험 입력 템플릿

`docs/templates/SPPS_Planner_V9_EXCEL_MULTI_SHEET_TEMPLATE.xlsx`는 실제 측정치가 없는 **빈 파일**이다. `Final Outcomes`, `Process Steps`, `HPLC-MS` 3개 데이터 시트와 `GUIDE`로 구성되어 있다. 자동 시트 탐색은 데이터 시트 3개만 큐에 넣으며 각 시트는 여전히 사용자 검토/승인을 거쳐야 저장된다.

## 숫자 입력 주의

유럽식 소수점 쉼표 `0,734`는 0.734로, `78,5%`는 78.5%로 읽는다. `1,234`처럼 천 단위 구분인지 소수점인지 구별할 수 없는 값은 추정하지 않고 결측으로 표시해 경고한다. 수득률·순도 및 정량 필드의 잘못된 값은 각 필드별 개수와 함께 경고한다.
