# SPPS Planner V3.0.0 개발 로드맵

V3.0.0은 검증된 V2 합성 계산과 Classic resin/아미노산 제어 UI를
보존하면서, 작업 관리·실시간 기록·ML·데이터 저장 계층을 확장한다.
가짜 데이터와 placeholder 기능은 사용하지 않는다.

## 1/6 — V3 기반과 혼합식 UI

- V2 안정 기준본과 독립된 V3 소스 트리
- V3 런타임·저장·Export·빌드 버전 정체성
- 공간 효율적인 native 상단 메뉴
- Work List 더블클릭 독립 Work Item 창
- 독립 창의 Plan 편집 → Apply Change → 연결 결과 재계산
- 기존 Classic resin/아미노산/chemistry 제어 유지

## 2/6 — 실시간 합성 실행·보정 기록

- **완료**
- 계획 단계별 실행 상태와 실제 투입량·단위·상태 기록
- 현장 Plan 수정, 사유, 작업자 메모, doubling 변경의 UTC 시간 기록
- `event_id`와 `work_item_id`를 가진 append-only 전후 이벤트 원장
- Undo가 과거 기록을 삭제하지 않고 반대 값을 적는 보상 이벤트로 동작
- 수정값이 기존 Apply Change를 통과해 Plan/Materials/Checklist/Total/Cleavage에 즉시 반영
- Project 저장·자동저장·로드에 실행 원장을 Work Item별로 함께 보존
- Stage 3에서 그대로 feature로 변환할 수 있는 lossless ML 레코드 제공

## 3/6 — 실제 기록과 ML 연결

- **완료**
- 합성 실행 원장과 최종 Plan에서 서열·공정·수정·doubling·상태·실투입 feature 자동 추출
- 실제 수율·crude purity·실패·doubling 필요성을 Work Item별로 검토 저장
- 결과 수정 시 기존 값을 지우지 않는 outcome review revision 이력
- 잘못된 HPLC integration·중단 run 등을 사유와 함께 학습에서 제외
- 내용 fingerprint 기반 불변 CSV dataset version과 manifest 생성
- target별 5개 이상의 included/reviewed 실제 값이 있을 때만 학습
- 실패·doubling 분류는 최소 2개의 실제 class가 있어야 학습
- 결과값을 feature에서 제거해 target leakage 방지
- 모델의 dataset version·fingerprint·평가 지표 metadata 저장
- 학습된 모델로 현재 Work Item 예측 가능

## 4/6 — Excel/HPLC 수준 데이터 시스템

- **완료**
- 기존 저장 파일을 자동 승격하는 Project → Work Item → 복수 Run 계층
- Run별 Plan·Materials·Total·Checklist·Cleavage·실행 원장·ML review 독립 보존
- JSON 원자적 저장, 마지막 정상 `.bak` 복구, 최근 프로젝트 12개 목록
- 외부에서 파일이 바뀐 경우 덮어쓰기를 거부하는 SHA-256 충돌 방지와 Save As
- Plan/Run/Event/ML/HPLC/Materials/Total/Checklist/Cleavage/History를 포함하는 다중 시트 XLSX
- `Column_Map` 시트와 API mapping을 이용한 사용자·장비 컬럼명 변환
- HPLC 결과 CRUD, 검색·정렬, 삭제 보존, 변경 사유와 전후 값 이력
- HPLC data/method 파일 경로·존재 여부·크기·수정시각·SHA-256 연결
- Waters·Agilent·Shimadzu 등에서 내보낸 CSV/XLSX의 일반적인 HPLC 컬럼명 자동 인식

## 5/6 — 합성 위험 경고

- **완료**
- 규칙 기반 chemistry 경고를 기본 안전망으로 유지
- 실제 누적 데이터가 있을 때만 ML 위험 점수 제공
- Aspartimide, aggregation, difficult sequence, 반복 결합 후보 표시
- 근거와 영향을 함께 제시하고 자동 적용하지 않음
- Cys/Met/Trp, 초기 Pro 문맥, 실행 failed/hold 기록 검토
- Run별 assessment revision, fingerprint, 사유 필수 acknowledgement 감사 이력
- 실제 classifier probability와 dataset version/fingerprint 연결
- Data Workbook 위험 검토 3개 시트 및 독립 Risk Report XLSX 왕복

## 6/6 — UI 완성·Windows 배포

- **완료**
- Modern/Classic 시각 통일과 공간 최적화
- 키보드 작업, 창 크기, 고해상도 화면 점검
- Windows 실제 GUI/EXE/Installer 검증 절차와 자동 계약 검사
- 전체 기능 회귀검사와 최종 사용자 매뉴얼
- Compact/Standard/Comfortable 표시 밀도와 1024×680 이상 반응형 중앙 배치
- Windows DPI awareness, 한·영 매뉴얼, 직접 연결된 키보드 단축키
- V3.0.0 EXE version resource와 Installer metadata 통일
- 삭제된 legacy hidden import 제거 및 Windows release contract 자동 검사
- Python/Inno Setup 탐지·설치부터 EXE/Installer까지 연결된 자동 빌드

## 현재 상태

Stage 6/6까지 구현 완료. V3.0.0 소스 완성본은 동일한 테스트·감사 기준과
Windows release contract를 유지한다. 실제 배포 EXE/Installer는 Windows
10/11에서 제공된 자동 빌드와 최종 확인 목록을 통과한 파일을 사용한다.
