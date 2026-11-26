# SPPS Planner V9.0.0 — Evolution: 다중 Excel·CSV와 AI 데이터 검증

> 개발 소스 증분 업데이트 (2026-11-09). 앱 버전은 **V9.0.0**을 유지한다. 기존 SPPS 계산 엔진 및 화학 규칙을 변경하지 않았다.

## 실제 추가·수정한 기능

1. **다중 파일 가져오기:** Excel `.xlsx`, CSV/TSV/TXT 여러 파일을 한 번에 선택한다. 첫 파일부터 **Check & clean → 데이터 확인 → 승인 체크 → Stage reviewed file / Next**를 수행한다. 다음 파일의 시트와 매핑은 별도로 검토한다. 마지막으로 Save combined data를 누른다. 한 파일만 선택한 기존 경로도 유지한다.
2. **저장 방식:** `Append`는 기존의 검증된 로컬 기록을 보존하며 새 관측값을 이어 붙인다. `Replace`는 검토한 데이터셋으로 바꾼다. 어느 방식도 중복 행이나 동일 Run ID를 자동 제거하지 않는다. 저장 전 전체 행 수와 중복 경고를 검토한다.
3. **품질 감사:** `Audit data quality`로 서열 인식 실패, 정확히 중복된 행, 중복·충돌 Run ID, 수득률/순도 실측값의 유효성 및 입력 필드 누락을 확인한다. 충돌 Run ID, 중복된 전체 관측 행, 해석 불가능한 서열이 있으면 ML 훈련을 보류한다. 동일한 Run ID가 별도의 실제 반복 실험을 의미한다면 식별자를 수정하여 재검토해야 한다. `LOT`만으로 실험 고유 ID를 자동 판정하지 않는다.
4. **로컬 백업:** 기존 데이터셋을 새로 저장하기 전 정상 사본을 `ai_excel_reviewed_v9.json.bak`로 원자적으로 기록한다. `Restore previous dataset`은 명시적인 확인 후 해당 마지막 백업을 복원한다. 원본이나 백업의 데이터 해시 불일치 시 복원·이어붙이기를 중단한다.
5. **유사 실험 탐색:** 기존 길이/몇 개 잔기 수만 비교하는 방식 대신 실제 서열의 잔기 순서를 반영한 삽입·삭제·치환 편집 거리를 사용한다. 최대 20,000개 자료에서 UI 정지를 줄이기 위해 조성 기반 후보를 먼저 골라 **근사적으로** 비교하며, 반환 결과에 편집 거리와 Resin·Coupling 일치 여부를 명시한다. **실험적 효과 유사성이나 적합한 합성 조건을 증명하지 않는다.**
6. **저해상도 GUI:** Mapping/Preview는 별도 스크롤 영역, 저장·학습·백업 복원·데이터 감사 버튼은 고정 하단 영역으로 구성한다. 다른 창의 공통 ttk.Treeview 스타일은 수정하지 않았다.
7. **추천 창 생명주기:** `ExperimentalDataWindow`의 스크롤 캔버스 목록을 초기화 단계에서 먼저 생성해, 비정상적인 초기화 경로의 `AttributeError`를 방지한다.

## 작업 순서

`Project Manager → Auto Plan (Optional) → AI · Import Excel / CSV`에서 실행한다.

1. 하나 이상의 파일 선택 → 각 파일의 자동 매핑 및 데이터 확인
2. 시트/퍼센트 변환을 확인하고 `Check & clean` → 승인 체크
3. `Stage reviewed file / Next`로 다음 파일 검토 (마지막 파일까지 반복)
4. `Audit data quality` → Append 또는 Replace 선택 → `Save combined data`
5. 새 데이터는 **실험 기록 원본 DB 및 활성 SPPS Plan을 변경하지 않는다**. 충분한 실측값이 있을 때만 별도 `Train local AI` 실행.

## 범위 및 제한

- 기본 `product_path` 구분이 없는 외부 데이터로 보호형/고리형 펩타이드 수득률을 자동 예측하지 않는다.
- 현재 모델은 로컬 scikit-learn Random Forest 기반의 **탐색적 회귀**다. 기존의 서열 그룹별 데이터 분리·baseline 대비 검증, 범위 밖 예측 보류 규칙을 유지한다.
- `joblib` 모델은 Python pickle 기반이다. 로컬 체크섬은 파일 변조 발견에 유용하지만 악의적인 모델의 실행 안전성을 보장하지 않는다. 외부 모델 파일을 복사하거나 실행하지 않는다.
- 잘못된 데이터도 사용자가 명시적으로 저장할 수 있으나, 품질 검사 실패 항목은 훈련에서 차단한다. Append는 관측값을 자동 평균하거나 중복 제거하지 않는다.
- 기존 데이터셋이 이미 손상된 경우 Append와 Replace는 백업을 무조건 덮어쓰지 않는다. 백업 복원 또는 기존 파일의 수동 복구가 필요하다.
- 실제 Windows 10/11 EXE/Installer의 빌드·설치·업그레이드·제거는 별도 검증이 필요하다. 테스트 환경과 실제 실험 검증은 구분한다.

## 변경 코드

- `suite_gui/ai_excel_core_v9.py`: audit, merge, append, backup/restore, residue-order similarity, training guard.
- `suite_gui/ai_excel_dialog_v9.py`: staged multi-file workflow, quality audit, append/replace, backup recovery, scrollable body with fixed actions.
- `suite_gui/modules/experimental_data_panel.py`: canvas list initialized before build.
- `tests/test_v9_evolution_multifile_quality.py`: 실제 버튼 동작, 품질 감사, 복구, 유사도, 작은 창 UI, 충돌 검사.

공개 ZIP에 실험 DB·실측 파일·학습 모델을 임의로 포함하지 않는다. Private 자료는 내부 전용이다.
