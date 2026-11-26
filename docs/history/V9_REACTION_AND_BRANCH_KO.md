# SPPS Planner V9.0.0 — Branch MW & Head-to-tail Reaction Method (개발본)

> **2026-11-07 검증 범위:** 이론적 분자량 및 작업자 입력 반응량의 검토 도구. 실험적 검증이나 승인 SOP, 실제 수율 예측이 아닙니다.

## 1. Auto Plan → Head-to-tail Method

1. Project Manager에 서열·Scale(mmol, 1 copy 기준)·Resin·Loading·Copies를 입력합니다.
2. `Auto Plan (Optional)` → `Final product`에서 `Head-to-tail — cyclic, still protected` 또는 `Head-to-tail — cyclic, globally deprotected`를 선택합니다.
3. `Side-chain groups`에서 보존을 *가정*할 보호기 정책을 선택합니다.
4. `Head-to-tail Method...` 버튼을 눌러 **Solution phase**의 반응법을 검토합니다. 기존 2-CTC selective cleavage를 실행했다는 의미가 아니라, 자유 N-terminus와 C-terminal COOH를 가진 보호형 Linear 중간체가 확보된다는 가정입니다.
5. 등록된 DIC/HOBt, EDC·HCl/HOBt, HATU/DIEA, PyBOP/NMM, DIC/Oxyma 중 시스템을 선택하고 **각 시약 eq, 농도(mM), 용매, 시간(h), 온도(°C)**를 직접 입력합니다. 어느 값도 자동 최적화되지 않습니다.
6. `Preview quantities`에서 **시약별 mmol**과 희석 용액량을 확인합니다. `Use as unapproved draft`로 검토 내용을 Auto Plan에 붙입니다. 입력을 생략한 경우 `INCOMPLETE_REVIEW_ONLY`로 보존됩니다.
7. `Generate Full Plan` 이후 Checklist의 `Head-to-tail cyclization — review`에 방법과 주요 입력을 기록합니다. **기존 Plan/Materials의 Coupling·Cleavage 계산을 이 반응법으로 자동 덮어쓰지는 않습니다.**
8. `Export Draft JSON`에는 사용자가 지정한 시약 역할·당량·중간체 MW·수득량 시나리오와 미검증 상태가 기록됩니다. 프로젝트 저장 시 `v9_mass_options.reaction_review`에 보존됩니다.

## 2. 반응량 계산

- 각 시약 `mmol per copy = Scale(mmol) × operator eq`.
- 용액 부피 `mL per copy = 1000 × Scale(mmol) ÷ Concentration(mM)` (균질 용액 가정).
- 여러 Copies는 **전체 사용량**과 한 Copy당 사용량을 구분합니다.
- 예를 들어 Scale=0.2 mmol, Copies=3, concentration=1 mM이면 **200 mL/Copy, 전체 600 mL**입니다. 이는 실험 권장 부피가 아니라 산술 결과입니다.
- 시약별 g/mL는 **정확한 bottle MW, 수화물 여부, 농도·밀도**가 확인되지 않아 계산하지 않습니다. `EDC·HCl`과 `EDC`는 다른 화학형이며, HOBt 수화물 여부도 별도로 확인해야 합니다.
- DIC·EDC·HATU·PyBOP는 결합 활성화 시약, HOBt·Oxyma는 additive, DIEA·NMM은 base로 기록합니다. 이들 모두를 catalyst로 표시하지 않습니다.

## 3. 보호형 Head-to-tail 질량

- 선택적 Cleavage 후 보호형 Linear MW와 Head-to-tail 보호형 Cyclic MW는 **이론상 물 1분자(18.01528 g/mol)** 차이입니다.
- N-말단 캡(Ac/Boc 등), C-terminal amide, 확인되지 않은 보호기 및 레진/말단 불일치는 Cyclization MW 계산을 차단합니다.
- 일부 Trt 등 산에 민감한 보호기가 실제로 유지될지는 별도 실험·분석이 필요합니다.
- `on-resin` Head-to-tail은 별도 free-acid linker 전략이 필요하므로 **지원하지 않습니다.** Solution phase, 선택적 Cleavage 후 중간체 기준의 계산만 제공합니다.
- Disulfide, Side-chain Lactam, Thioether, Click, RCM은 이 모듈에서 **미지원**이며 원자별 연결 위치 없이 자동 MW나 시약량을 생성하지 않습니다.

## 4. 제한적으로 추가한 Branch 제품 MW

- **지원 조건:** `K(GGEP)`처럼 단일 Lys의 ε-amine에 표준 **L형 천연 아미노산 1-letter 서열**이 한 가닥 연결되는 단일 Branch.
- `K(Dde)(GGEP)`처럼 Lys의 선택적 보호기가 합성 중 제거된다고 명시된 경우, 그 **제거된 보호기 질량은 최종 제품에 남지 않는 것으로 계산**합니다.
- Branch의 전체 이론 MW는 자유 Lys-amine과 Branch arm의 C-terminal COOH가 amide 결합을 형성하면서 탈수된다는 화학량론을 적용합니다. Catalog precursor 보호기들은 보존을 가정합니다.
- **미지원:** 다중 분지, non-Lys 분지, side-chain이 추가로 변형된 Branch arm, D-amino-acid Branch, 복합 Branch+Cyclization, C-terminal attachment 구조가 불명확한 표기.
- **Checklist 단계별 Branch MW는 의도적으로 공란/경고**로 두었습니다. 현재 Main Chain/Branch 합성 순서와 매 단계 보호기 상태를 검증할 원자 연결 모델이 없으므로 최종 제품 MW를 중간 MW에 잘못 대입하지 않습니다.

## 5. 수득량

기존 V9 수득량은 사용자 입력 coupling conversion × cyclization recovery × isolation recovery의 **시나리오 계산**만 유지합니다. 반응 Method 선택이 수율·순도·성공 확률을 자동 예측하지 않습니다. Branch 전체 MW가 계산되더라도 실제 Branch Coupling 단계 수와 회수율을 확인하기 전에는 이론량 이외의 예측을 신뢰하지 마세요.

## 6. 배포·검증

V9.0.0 표기를 유지하며 기존 data schema(`SPPS data v6.0.0`)는 수정하지 않습니다. Tkinter Main UI와 계산 엔진의 기존 기본 공정을 유지하고 새로운 반응법은 선택적 검토 데이터로만 저장합니다. 실제 Windows GUI/Installer와 실제 선택적 Cleavage·Cyclization의 결과 검증은 별도로 필요합니다.
