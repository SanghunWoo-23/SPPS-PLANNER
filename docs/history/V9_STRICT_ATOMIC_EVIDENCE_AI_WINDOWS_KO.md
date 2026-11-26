# SPPS Planner V9.0.0 — Strict Chemistry, Evidence AI & Windows QA (2026-11-11)

## 변경 사항 — 실제 소스 구현

1. **원자 매핑 Topology 입력 엄격화:** 알 수 없는 필드, 고리화 옵션 오타, Boolean 대신 문자열, 단일 체인과 다중 체인 중복 선언, 반응 유형별 누락 원자 참조를 거부한다. 입력 JSON의 정규화된 SHA-256으로 구조 검토 식별자를 계산한다.
2. **반응별 질량 수지:** RDKit 분자 그래프의 반응 전·후 정확질량 차이를 H₂O, H₂, HX, C₂H₄, 또는 원자보존 반응의 이론적 차이와 독립 대조한다. 일치하지 않으면 제품 MW를 반환하지 않는다. 계산 성공은 **합성 성공이나 반응 선택성 증명과 다르다**.
3. **GUI 증거 반영:** 독립 구조 검산 실패가 났을 때 `Attach review to Auto Plan`로 실패 결과가 추가되지 않도록 수정. 사용자 정의 원자 그래프에 대한 기존 검토·승인 경로는 유지한다.
4. **논문 검색 + 명시적 생성 AI 검토:** 로컬 PDF/TXT/MD 발췌문 검색 후 사용자가 실제 전송할 문장·페이지·문서 해시를 미리 본다. 별도의 동의 버튼을 누른 경우에만 OpenAI Responses API로 **선택된 발췌문만** 전송한다. 기본값은 오프라인. `OPENAI_API_KEY`와 `SPPS_LITERATURE_AI_MODEL` 환경변수 필요. `store=false`를 요청하며 별도의 API 과금이 가능하다. 인용 문구가 원문에 정확히 존재하지 않으면 결과를 거부한다. AI 문장은 검증된 SOP나 실험 결과가 아니다.
5. **Windows 실설치 검증 설계:** `--gui-smoke`가 설치된 실행 파일의 실제 Tkinter 창 생성·이벤트 처리·종료를 시도하고 JSON 증거를 기록한다. 설치 수명주기 CI는 임시 격리 데이터 생성 → Installer 설치 → EXE self-test → GUI smoke → 제거 → 사용자 파일 보존 검사를 시행하도록 확장했다. CI 증거 JSON을 artifact로 남긴다. 실제 Windows 성공 실행 로그는 아직 없다.
6. **실행 중 monkey-patch 방지:** `tools/audit_monkey_patches.py`로 런타임 클래스 바인딩 0건 확인. **pytest의 `monkeypatch` 픽스처는 테스트 격리용이므로 런타임 패치와 구별한다.** 실행 화학 엔진은 변경하지 않는다.

## 이번 작업의 실제 확인 결과

- Public: Linux Xvfb 전체 테스트 **760 passed / 3 skipped / 0 failed** (변경 소스에 대해 확인).
- Private: V9 테스트 **241 passed**, 나머지 구형 테스트 **521 passed / 1 skipped** (분할 실행); 단일 전체 실행은 종료 지연으로 완료로 기록하지 않는다.
- 구조 검증·선택형 AI 기능: 실제 API 호출 대신 모의 전송 경로 및 원문 인용 검사 테스트. 임의 생성한 합성 데이터는 실제 외부 실험 성능이 아니다.
- GUI: `--gui-smoke` Linux Xvfb에서 PASS. 실제 설치 GUI 동작 및 안정적인 장시간 사용을 Windows에서 확인한 것은 아니다.
- 정적 Windows 소스 계약, Python compile, self-test, Manifest·ZIP 무결성은 최종 패키징 시 별도 확인한다.

## 실행 및 재현 방법

```powershell
python main_launcher.py --self-test
$env:SPPS_PLANNER_USER_DATA = "$env:TEMP\spps-v9-gui-smoke-data"
$env:SPPS_PLANNER_GUI_SMOKE_OUTPUT = "$env:TEMP\spps-v9-gui-smoke.json"
python main_launcher.py --gui-smoke
python -m pytest -q
```

논문 AI는 프로그램의 `Local literature evidence`에서 문서 검색 후 **AI review selected excerpts...**를 눌러 실제 전송 내용을 미리 확인하고 동의한다. API 설정이 없으면 외부 전송 없이 오류가 표시된다.

Windows 설치 검증은 안전한 별도 Windows CI 작업 환경에서 실행하도록 준비했다. Source ZIP에는 완성된 EXE·Installer가 포함되지 않으며, GitHub Actions를 실행해야 실제 Windows 결과가 생성된다.

## 미완료 / 근거상 완료 판정 불가

- 특정 공급업체의 비천연 아미노산·보호기 분자 구조 검증은 구조식·분석 자료가 있어야 가능. 사용자 제공 원자 매핑 SMILES의 화학적 정체성과 결합 선택성은 자동으로 인증하지 않는다.
- 실제 독립 실험 데이터가 없으므로 수득률·순도 모델의 외부 예측 정확도 및 통계적 범위를 확인할 수 없다.
- 생성형 AI 통합은 **선택 발췌문** 기반이고, 외부 API 실호출·논문 전문 자동 해석 정확도·검증된 SOP 생성은 입증하지 못했다.
- Windows 네이티브 Installer·EXE·업그레이드·제거·장시간 사용 시험은 설정과 검증 스크립트를 구현했으나 실제 Windows 실행 증거가 없다.
- 어떤 소프트웨어도 모든 입력·환경에서 완전 무오류를 보증할 수 없다. 실패는 오류 메시지 및 검증 보류로 처리한다.

## 출처 및 기술 기준

- RDKit Book — 분자 유효성 검사, 원자가/입체화학: https://www.rdkit.org/docs/RDKit_Book.html
- OpenAI Responses API — 구조화된 출력 및 API 사용: https://platform.openai.com/docs/api-reference/responses
- scikit-learn model persistence: https://scikit-learn.org/stable/model_persistence.html

**라이선스:** 기존 SPPS Planner 사용자 정의 LICENSE를 유지한다. RDKit 등의 외부 소스 코드는 복사하지 않고 공개 API를 사용하며, 재배포 시 각 의존성 라이선스 고지를 확인한다. Public ZIP만 GitHub 공개. Private 실험 시드·개인 DB는 공개 금지.
