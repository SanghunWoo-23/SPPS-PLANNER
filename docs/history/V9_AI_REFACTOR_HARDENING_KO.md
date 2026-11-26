# SPPS Planner V9.0.0 — AI·Excel 코드 정밀 개선 (2026-11-08)

## 적용 범위

이 문서는 V9.0.0 **AI/Excel Assistant 안정성 개선 개발본**에 적용된다. 앱 버전 표기는 `V9.0.0`을 유지하고, 기존 `engine.py`/화학 계산/Project Manager의 Generate 계약 및 저장 데이터 스키마는 유지한다. Public/Private는 서로 다른 사용자 데이터 프로필과 기존 비공개 파일을 보존한다.

### 변경 사항

1. **서열 식별의 화학적 정확성:** `H-Ser(tBu)-OH`, `H-D-Ser(tBu)-OH`, `[Fmoc-D-Arg(Pbf)-OH]`, 비대괄호 `Fmoc-D-Arg(Pbf)-OH`, `D-Ser(tBu)-D-Val`을 첫 글자로 오인하지 않고 독립 잔기로 해석한다. D/L 잔기, 단일 Lys 분지의 암 길이, Nle·Orn·Aib 등 비표준 토큰은 별도 ML 특징으로 계산한다. 해석 불명 토큰 및 D-비천연 일부 표기는 추측하지 않고 ML 보류로 처리한다. **서열 파서 원본 또는 화학 MW 엔진은 변경하지 않았다.**
2. **평가 데이터 누출 방지:** 동일한 펩타이드를 `ACD`, `A-C-D` 등으로 다르게 적어도 같은 서열 그룹으로 묶는다. 동일 그룹이 학습/검증에 동시에 포함되지 않도록 grouped holdout을 3회 적용하고, 2회 이상 중앙값 기준 모델보다 나아야만 탐색적 ML 모델을 보존한다. 홀드아웃 점수는 실제 예측력의 임상·실험적 보증이 아니다.
3. **Excel 파일 보호:** 12 MB 원본 제한 외에 XLSX 내부 압축 해제 크기 128 MB, ZIP 항목 1,500개를 제한한다. 검토한 파일이 저장 직전에 수정되면 승인을 무효화하고 다시 확인하도록 한다.
4. **검토 데이터 무결성:** 저장된 JSON 레코드의 정규화 SHA-256을 로드 시 다시 계산하여 불일치를 감지한다. 파일 깨짐·유효하지 않은 메타데이터에서는 안전하게 데이터를 거부한다.
5. **ML 모델 방어적 검증:** 기존 V9 모델의 이전 feature schema를 자동 적용하지 않고 재학습을 요구한다. 잘못된 모델 메타데이터·서명 변경·심볼릭 링크·비정상 큰 모델을 거부한다. 재학습 결과가 기준 모델보다 나쁘면 이전 승인 메타데이터를 보류 상태로 갱신한다.
6. **반응/UI 방어:** Reaction Method는 Boolean/객체를 수치·용매처럼 받지 않으며, 저장된 시약명의 비정상 자료형과 중복을 명확한 검증 오류로 반환한다. Auto Plan에서 Cyclic/보호형 제품을 선택한 경우 토폴로지 컬럼이 없는 Excel 데이터로 학습된 모델의 수득률 예측을 표시하지 않는다. 제품 유형 변경 시 이전 AI 근거를 제거한다.
7. **데이터 품질:** 완전히 동일한 행은 자동 삭제하지 않고 중복 경고를 표시한다. 결측 categorical 값은 `nan` 문자열이 아닌 빈 값으로 해석한다. 유사 실험 비교도 D형·비표준·Branch 특징의 차이를 반영한다.

### 제한과 사용 주의

- **기존 학습 모델을 재학습해야 함:** 기존 `ai_excel_reviewed_v9.json`의 데이터 포맷은 그대로 사용하되, `ai_excel_(yield|purity)_v9.joblib`는 새로운 특징량 구성을 지원하지 않아 자동 비활성화한다. 프로그램의 AI 창에서 Train local AI를 다시 수행한다.
- Local ML은 여전히 **실험 결과 보조 분석**이며 시약·당량·반응 조건 또는 SOP를 자동 승인하지 않는다. 불충분한 데이터에서는 모델을 만들지 않으며 유사 실험 검색만 제공한다.
- `joblib`은 Python 역직렬화 포맷이므로 신뢰할 수 없는 외부 모델 파일을 사용자 프로필로 복사하지 말 것. checksum은 우발적 파일 변조를 감지할 뿐 공격자가 메타데이터와 파일을 동시에 바꾼 경우의 보안 보증이 아니다.
- 지원되는 파일 형식은 `.xlsx`, `.csv`, `.tsv`, `.txt`이며 실측 수득률·순도가 별도 확인되지 않는 데이터에 자동으로 타깃을 지정하지 않는다.
- 실제 Windows EXE·Installer 설치, 전체 GUI 조작성, 실제 실험 수득률 예측 정확도는 별도 검증이 필요하다.

### 테스트

핵심 검증은 `tests/test_v9_ai_excel_import.py`와 새 `tests/test_v9_ai_excel_refactor_guards.py`. 두 분기의 전체 테스트 결과는 최종 외부 QA 보고서로 별도 기록한다.

```bat
python -m pytest -q tests/test_v9_ai_excel_import.py tests/test_v9_ai_excel_refactor_guards.py
python main_launcher.py --self-test
python tools\verify_windows_release.py
```
