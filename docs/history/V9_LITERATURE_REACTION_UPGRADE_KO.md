# SPPS Planner V9.0.0 — 문헌 기반 Reaction Evidence 고도화 (2026-11-08)

## 개발 범위 / 검증 경계

- **코드 구현:** `spps_planner/reaction_evidence_v9.py`에서 참고 논문 ID·PMID/DOI·연도·URL·적용 범위·위험 설명을 관리한다. `reaction_planner_v9.py`에서 반응 초안을 만들 때 이를 자동 첨부한다. `reaction_method_editor_v9.py`에서 위험·참고 문헌을 미리 보여준다.
- **기계 판독 데이터:** `docs/REACTION_LITERATURE_V9.0.0.json`은 런타임 내장 데이터의 감사용 복사본. 테스트가 내장 데이터와 JSON이 정확히 일치하는지 검사한다.
- **지원 범위:** **Solution-phase Head-to-tail Cyclization의 검토 초안**에 문헌 근거와 위험 경고 추가. 다른 Cyclization 방식의 계산은 여전히 지원하지 않으며 잘못된 MW를 생성하지 않는다.
- **확정하지 않는 값:** 자동 최적 당량, 반응 시간, 유효 농도, 수율, 순도, 회수율, 성공 확률. 사용자가 입력한 조건은 실험 SOP로 자동 승격되지 않는다.

## 근거별 프로그램 반영 사항

| 문헌·연도 | 문헌이 실제로 지원하는 내용 | 프로그램 반영 | 주의 |
| --- | --- | --- | --- |
| Barlos 1991, PMID 1917309 | 2-CTC에서 온화한 절단으로 일부 측쇄 보호기 유지 가능 | `CTC_SELECTIVE_CLEAVAGE_REVIEW` | 모든 보호기의 유지·모든 용매 조합으로 일반화 불가 |
| McMurray 1994, PMID 7696839 | On-resin head-to-tail에서 올리고머화·라세미화 가능, sequence/solvent/support 영향 | `CYCLIZATION_OLIGOMERIZATION`/`CYCLIZATION_EPIMERIZATION` | 용액상 조건에 직접 수율 적용하지 않음 |
| Malesevic 2004, DOI 10.1016/j.jbiotec.2004.03.015 | 용액상 Cyclization의 경쟁 분자간 반응과 pseudo-high dilution 검토 | `CYCLIZATION_OLIGOMERIZATION` | 수치화된 성공률·임의 농도 추천 없음 |
| Cheneval 2014, DOI 10.1021/jo500699m | 2-CTC에서 부분 보호형 linear → cyclic → 탈보호 → Cys 산화 경로 | `CYS_ORTHOGONAL_OXIDATION_REVIEW` | 모든 Cys 서열의 disulfide 형성 자동 계획 아님 |
| Bouayad-Gervais 2022, DOI 10.1002/pep2.24254 | 측쇄 보호형 linear의 용액상 macrocyclization 및 MS/MS 판독 | Head-to-tail 경로의 근거 문헌 | 시퀀스별 정량 수율 일반화 금지 |
| Erny 2020, DOI 10.1021/acs.oprd.0c00227 | DIC/Oxyma의 DMF 중 HCN 생성 및 완화 연구 | DIC/Oxyma 선택 시 높은 위험도 경고 | 다른 용매 선택이 자동 안전 판정은 아님 |
| Manne 2021, DOI 10.1021/acs.orglett.1c02466 | Carbodiimide와 Oxyma의 부반응이 시약 구조에 의존 | DIC/Oxyma 위험 보강 | 다른 Coupling 시스템에 HCN 위험을 무차별 할당하지 않음 |
| Kong 2025, DOI 10.1002/cbic.202500490 | Aspartimide는 Fmoc base-deprotection에서 유의할 부반응 | Asp 서열일 때 `ASP_FMOC_DEPROTECTION` | 경고는 실제 부반응 발생이나 실패 확률이 아님 |

## 작업 예시

1. `dS-dV-dS` + `2-CTC` + Head-to-tail을 선택하면 선택적 절단, 분자간 반응, 라세미화 관련 문헌 경고를 출력한다. 2-CTC에서 남겨야 할 tBu 등의 보호기 상태는 **계산 가정**임을 계속 표시한다.
2. `DIC/Oxyma`를 선택하면 용매가 DMF인지와 무관하게 HCN 위험 문헌을 안내하되, DMF에서의 실험적 관찰을 명시한다.
3. `D-S-C` 같은 Asp/Cys 포함 서열은 Aspartimide 위험 및 Cys 후속 처리 검토 경고를 추가한다.
4. 기존 미리보기처럼 시약별 당량·농도·시간은 사용자가 입력하고, 미입력 시 `INCOMPLETE_REVIEW_ONLY`이다. JSON 저장·복구 시 문헌 내용이 변조되거나 구버전이라면 새 검토가 필요하다.

## 한계 및 실험 검증

- 반응 위험 경고는 문헌 기반 일반 경고이지 합성 결과 예측이 아니다.
- HOBt/Carbodiimide 등 시약 취급 안전성은 최신 SDS·기관 안전 지침을 우선한다.
- 조건의 실제 타당성과 HPLC/LC-MS로 확인되는 반응 진행도, 입체화학, Dimer 검출은 별도 검증 대상이다.
- 이번 변경으로 기존 SPPS 기본 Coupling 계산값, `mass_balance_v9`, 수득률 알고리즘을 수정하지 않았다.
- Windows 네이티브 EXE/Installer 검증은 Linux headless 및 가상 GUI 시험으로 대체할 수 없다.

## 자료 무결성

`reaction_evidence_v9.py`를 변경하면 `REACTION_LITERATURE_V9.0.0.json`도 새로 생성하고 `tests/test_v9_reaction_literature_evidence.py`를 반드시 통과해야 한다. `reaction_review` 저장 포맷에 `literature_evidence`가 추가되었으므로 오래된 미리보기 기록은 재검토 필요가 정상 동작이다. 앱 버전은 V9.0.0 유지.

## 반응 중 Dimer / Cyclodimer 질량 검토

Bouayad-Gervais et al. (2022)은 cyclic target의 분석에서 올리고머 부산물의 구별이 중요함을 보여준다. V9 Auto Plan의 Head-to-tail Method 미리보기에는 보호형 Linear의 **평균 중성 MW** `M`에서 다음 두 후보를 구분해 표시한다.

- 한 번의 분자간 amide 결합을 만든 선형 이량체: `2 M − H2O`.
- 두 번의 결합으로 고리형 이량체를 만든 경우: `2 M − 2 H2O`.

이는 이상화된 작용기 원자수지에 따른 **분석 후보 질량**이며 실제 부산물 형성, LC-MS `m/z`, 프로톤화/염착/동위원소 패턴, 수율을 예측하지 않는다. 기존 분자량 모델이 적용 불가한 경우에는 이 후보도 제공하지 않는다.
