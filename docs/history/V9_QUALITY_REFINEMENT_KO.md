# SPPS Planner V9.0.0 — 코드 안정성·검증 개선 기록

**개발 빌드, 2026-11-08. 정식 Windows/실험 검증 전.** 프로그램 버전은 `V9.0.0`이며 저장용 `SPPS data v6.0.0` 스키마 표기는 기존 프로젝트 호환을 위해 보존했다.

## 변경 사항

1. Auto Plan의 `Copies`가 `1.5`, `NaN`, `Infinity`, 논리값 등을 정수로 조용히 변환하던 위험 제거. 수득량 계산의 coupling 단계 수에도 동일한 검증 적용.
2. Head-to-tail Method의 저장/재사용 시 서열, 레진, 보호기 정책, Scale, Copies, Method, 당량, 계산량과 상태를 현재 코드로 재계산한다. 손상·변조·오래된 반응 설정은 거부하고 재검토를 요청한다. 사용자가 승인한 실험 SOP로 승격하지 않는다.
3. 작은 비영(非零) mmol/희석부피는 유효숫자를 보존하고, 극단적 입력에 의해 무한대가 생기면 안전하게 오류 처리한다.
4. Head-to-tail Method 편집기에서 시약 시스템을 바꾸었다 돌아와도 입력 중인 eq를 보존한다.
5. Auto Plan 창에서 마우스 휠로 스크롤할 수 있다. 전역 이벤트 바인딩이나 `ttk.Treeview` 전역 스타일은 변경하지 않는다.
6. 수득률 시나리오에 입력 컨텍스트를 저장하고 일치할 때만 편집값을 복원한다. 수득률은 사용자가 제공한 입력값 기반 산술이며 실험적 예측이 아니다.
7. 패키징된 앱에서도 `python main_launcher.py --self-test`를 통해 V9 핵심 계산·반응 설정 검증을 수행하도록 변경했다.

## 변경하지 않은 중요한 원칙

- `engine.py`의 기존 SPPS 화학량론과 Plan/Materials 계산을 변경하지 않음.
- 선택적 Cleavage로 보호기를 유지하는 효과는 **이론상** 계산이며 실제 보호기 잔존 여부를 검증하지 않는다.
- Branch 제품 전체 MW는 지원 범위가 제한되어 있고, 복잡한 Branch/Cyclic 단계별 MW를 만들어 내지 않는다.
- Head-to-tail 반응 시약 Method는 검토용이며 생성된 Plan/Materials를 자동으로 수정하지 않는다.
- Public/Private 프로젝트 데이터는 물리적으로 분리하여 배포하고, Private 데이터는 공개하지 않는다.

## 검증 방법

```bash
PYTHONPATH=.:apps/spps_planner_app python -m pytest -q
PYTHONPATH=.:apps/spps_planner_app python tools/verify_windows_release.py
PYTHONPATH=.:apps/spps_planner_app python main_launcher.py --self-test
```

각 검사 결과는 해당 빌드의 외부 인수인계 보고서에 별도 기록한다. Python 3.13/Linux의 검사 성공이 Python 3.11/3.12 Windows EXE/Installer 실사용 성공을 보증하지 않는다.
