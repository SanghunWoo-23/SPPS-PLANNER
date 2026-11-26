# SPPS Planner V9.0.0 — 현재 기능·검증 상태

이 문서는 **V9.0.0 소스 개발본의 현행 기능 안내**입니다. `docs/history/` 문서는
당시 시점 기록이므로 현재 지원 범위와 충돌하면 이 문서를 우선 확인합니다.
실제 지원 가능한 구조는 입력 조건 및 자동화 테스트에 따라 제한됩니다.

| 분야 | 구현된 경로 | 여전히 검증이 필요한 내용 |
| --- | --- | --- |
| 기본 SPPS | Project Manager, Plan, Materials, Checklist, Generate/Apply, Workup | 실제 작업 SOP 적합성 |
| 화학·MW | 지원되는 서열·보호기·Lys 분지/고리형 계산, 조건부 RDKit 원자구조 교차검산 | 모든 비천연 잔기 및 복잡한 결합의 완전한 실험적 검증 |
| Custom topology | 명시적 Monomer/원자 매핑 구조 입력, 제한된 반응 유형의 이론 구조·질량 검산 | 선택성, 촉매 및 실제 반응 수율/성공률 |
| MS | 지원 제품에 대한 정확질량 및 이론 m/z 후보 | 실제 LC-MS 피크의 구조 동정 |
| Auto Plan | 사용자 검토 기반 조건 초안, 일부 구조·근거 검토 | 모든 반응의 자동 최적화·검증 SOP |
| Excel/CSV | 다중 파일·다중 시트 검토, 컬럼 검사 및 승인 후 데이터 저장 | 외부 원본 데이터 자체의 진위 |
| AI/ML | 로컬 모델, 준비도/유효성 점검, 단계별 지표, 별도 외부 데이터 평가 | 실측 외부 배치에서 재현성·성능 입증 |
| 문헌 | 로컬 문헌 검색, 동의 기반 선택적 외부 AI 분석 | 생성형 요약의 과학적 정확성 및 자동 SOP 승인 |
| Windows | 소스·빌드 설정·CI 스크립트 및 Linux 가상 GUI 테스트 | 실제 Windows EXE·Installer 설치/삭제/장시간 운용 결과 |

**주의:** 합성 반응이 가능하다는 판정, 수율 보장, 제품 확인 및 의학적 판단에
사용할 수 없습니다. 사용자가 검토·승인해야 하며 실제 실험으로 확인해야 합니다.
실제 설치 및 실험 검증을 하지 않았다면 Release에는 `NOT_TESTED`로 기록합니다.

- 사용자 안내: [한국어 매뉴얼](USER_MANUAL_KO.md)
- 내부 파일 구성: [소스 레이아웃](SOURCE_LAYOUT_KO.md)
- 지난 개발 기록: [historical docs](history/README.md)

## 소스 배포 텍스트·버전 계약 검사

`python tools/audit_release_text_v9.py`는 현행 README, Windows 단일 BAT,
Installer 설정, `VERSION`, 내부 `.txt` 및 RDKit 의존성 설명의 일치 여부를
검사합니다. **Windows 설치 또는 실험 결과를 검증하는 시험이 아닙니다.**

## 2026-11-26 — V9.0.0 실험 데이터 축적·검증 안정화

**버전은 V9.0.0을 유지합니다.** 기존 Linear / Branched / Cyclic 계산,
Materials, Checklist, AI 모델 학습·승인 절차는 변경하지 않았습니다.

- Recommendations & Lab History에서 **Start Experiment → Add Result**를 사용합니다.
  최종 Cleavage의 조건 기록과 결과(실측 수득률·순도)는 동일한 SQLite
  트랜잭션으로 저장하며 한쪽만 기록되는 반쪽 저장을 방지합니다.
- 측정값은 유한·비음수여야 하고 순도는 0–100%여야 합니다.
  100% 초과 수득률은 실제 crude 물질의 수분·염 등 영향일 수 있으므로
  삭제하지 않되 재검토 전에는 `incomplete`로 저장합니다.
- Advanced → Data Health에는 측정값이 있는 검증 기록 수, 독립 Run 수,
  고유 서열 수, 유실된 연계 정보, 중복 의심 Run/단계 및 검토 필요 데이터를
  표시합니다. **건수나 검증 상태만으로 예측 정확도를 보장하지 않습니다.**
- Advanced → Data Health → **Export Verified QC CSV**는 실측으로 기록하고
  운영자가 검증한 수득률·순도만 검토용 CSV로 내보냅니다. 이후 기존
  **Import Excel to AI & ML** 창에서 명시적으로 검토·승인한 경우에만
  로컬 AI 데이터로 저장할 수 있습니다. 내보내기 자체는 모델 학습을
  수행하거나 SQLite 기록 상태를 변경하지 않습니다.
- CSV의 `planned_scale_mmol`과 `planned_resin`은 냉동된 Plan 참고값입니다.
  실제 수행값인 `scale_mmol`/`resin`, 제품 형태 `product_path`,
  결합 시스템 `chemistry`는 **추측하지 않고 빈칸**으로 두었습니다.
  실험 노트를 확인해 운영자가 직접 채운 후 AI 데이터 품질 검사와
  중복 Run 검사를 거쳐야 합니다.
- Public/Private별 실험 데이터는 각 프로필의 별도 저장소를 계속 사용합니다.
  Private의 결과를 Public 자료로 공유할 때는 소유자 검토와 허가가 필요합니다.

**남은 실사용 검증:** Windows에서 설치/삭제, 실제 EXE 실행,
장시간 사용 및 현장 실험 결과에 대한 모델 외부 검증은 수행되지 않았습니다.
실측 데이터가 부족하면 AI 모델은 제한/보류되어야 합니다.

- 대량 누적 Loading 기록의 동일 조건 중위수 기반 Leave-one-out MAE는 기존 계산값을 유지하며 반복 재정렬을 줄였습니다. 이 MAE는 모델의 외부 검증 정확도가 아닙니다.
