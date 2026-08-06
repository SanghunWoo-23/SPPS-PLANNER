# V3 합성 위험 검토

`Risk Review`는 합성 Plan을 자동으로 바꾸는 처방 기능이 아니라, 작업자가
서열·Plan·Run 기록을 함께 검토하도록 돕는 독립적인 triage 계층이다.

## 규칙 기반 기본 안전망

- Aspartimide 후보 Asp-X 문맥
- 긴 소수성 구간과 낮은 전하 비율에 따른 aggregation 후보
- β-branched/Pro/인접 bulky residue/비표준 잔기의 difficult coupling 후보
- Cys 보호기·산화·disulfide 상태 검토
- Met/Trp 산화 민감성 검토
- resin 근처 초기 Pro 문맥 검토
- 현재 Plan의 repeat/doubling과 과거 Run의 failed/hold 기록

각 finding은 심각도, 위치, 관찰 근거, 가능한 영향, 검토 권고를 따로
제공한다. `rule_score`는 규칙별 가중치 합계인 우선순위 점수이며 실패
확률이 아니다. 권고 문구는 SOP/SDS·분석자료·작업자 판단을 대신하지 않는다.

## 실제 데이터 ML 신호

ML은 검토·포함된 실제 결과가 최소 5건이고 분류 class가 2개 이상인
데이터로 만들어진 `failure_flag` 또는 `doubling_required` 모델이 있을
때만 표시된다. 화면에는 prediction, 실제 classifier probability/confidence,
학습 행 수, dataset version/fingerprint가 연결된다. 모델이나 metadata가
없거나 유효하지 않으면 `ML unavailable`로 표시하고 임의 점수를 만들지 않는다.

## 기록과 데이터 왕복

- `Save Assessment Version`: 내용 fingerprint가 달라질 때만 새 revision 저장
- `Acknowledge Selected`: 사유가 필수인 별도 감사 이벤트 저장
- Project → Work Item → Run별 assessment/revision/acknowledgement 분리
- 전체 Data Workbook의 `Risk_Assessments`, `Risk_Findings`,
  `Risk_Acknowledgements` 시트로 export/import 왕복
- 별도 Risk Report XLSX로 summary/findings/ML signals/acknowledgements 출력

위험 검토 기능은 `Selected Plan`을 수정하지 않는다. 실제 수정이나 doubling은
기존 `Run / Corrections`에서 사유와 함께 수행한 뒤 `Apply Change`를 통해
Materials, Total, Checklist, Cleavage, Export에 반영한다.
