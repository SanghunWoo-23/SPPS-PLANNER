# SPPS Planner V9.0.0 — Sharp Atomic & Evidence Extension (2026-11-11)

> **개발용 코드**. 기존 Step 1/2·Generate·Apply Change·시약량 계산 엔진을 대체하지 않는다. 분자 그래프 검증은 **이론적인 연결 구조와 질량 계산**일 뿐, 합성 성공·보호기 선택성·수율·순도·구조 동정을 증명하지 않는다.

## 새 기능의 정확한 범위

- **사용자 정의 Fmoc-free / 보호형 / 비천연 아미노산:** 실제 원자 구조를 포함한 RDKit atom-mapped SMILES에서 평균 중성 MW, 정확질량, 분자식, 이론 `m/z`를 계산한다. Ala·Ser(tBu)·Lys(Boc)·Aib·Nle 등 예시가 포함된다. **Pbf·Dde 등은 완전한 보호형 SMILES를 사용자가 입력·검토하면 구조로 표현할 수 있지만, 이름만 보고 구조를 자동 생성하지 않는다.** 공급업체 SMILES·입체화학의 사실 여부는 실험자가 확인해야 한다.
- **복합 토폴로지:** 주쇄와 분지 Arm을 별도 `chains`로 등록한 뒤 명시된 두 반응 원자를 연결한다. 원자 매핑과 결합 검증으로 임의 위치의 여러 Amide 연결과 고리화, Cys–Cys Disulfide, Alkyl-halide 치환형 Thioether, 카보닐 공액 Thiol–Michael, 1,4-CuAAC, 말단 Alkene RCM의 **이론 생성물 그래프**를 계산한다. 화학 선택성, 입체화학의 반응 중 유지, 촉매·시간·당량 최적화는 미검증이다. SPAAC·1,5-CuAAC·특수 비정형 반응은 아직 자동 반응 템플릿이 없다.
- **분자량 흐름:** 각 반응 후 분자식·평균 MW·정확질량, 이론 양·음 이온 `m/z`를 구한다. 레진에 결합한 중간체의 실측 질량이나 실제 LC-MS 피크가 아니다.
- **Monomer 데이터 가져오기:** `token, smiles, source` 컬럼을 가진 `.xlsx`, `.csv`, `.tsv`, `.json`을 가져와 각 원자 구조를 확인한다. 중복 토큰과 잘못된 구조는 거부·표시하며 절대 자동 덮어쓰지 않는다. `token`을 넣은 topology JSON은 **검증한 카탈로그 항목**을 참조해 계산할 수 있다.
- **논문 전문 로컬 검색:** 사용자가 직접 선택한 PDF/TXT/Markdown의 텍스트 레이어를 검색해 문서명·페이지 번호·짧은 원문 인용을 제공한다. 스캔 PDF는 OCR 없이 `읽을 수 없음`으로 처리한다. 전문의 기계적 검색과 생성형 연구 해석은 별개의 기능이다. 원문 수치에서 자동으로 실험 SOP를 만들지 않는다.
- **Windows CI:** Windows EXE 생성 후 자기검사, 샌드박스 CI에서 Installer 자동 설치·자기검사·제거를 수행하는 스크립트 제공. **워크플로를 실제 실행해 성공한 로그는 아직 없다.**

## 사용 경로

`Project Manager → Auto Plan (Optional) → Independent molecular graph / Cross-link... → Custom atom-mapped JSON...`

1. `docs/examples/*.json` 예시를 열고 원자 매핑과 토폴로지를 이해한다.
2. `Load JSON...` 또는 `Import AA Catalog...`를 사용하고 구조·서열·입체화학을 확인한다.
3. `Compute atomic graph`로 계산. 오류가 있으면 `WITHHELD`와 사유만 표시한다.
4. 구조가 실제 목표 제품에 맞는다고 직접 확인한 경우에만 `Attach review to Auto Plan`을 선택한다.
5. Checklist는 저장된 MW가 아니라 **등록 구조를 다시 RDKit으로 계산해** 일치하는 경우에만 이론 값을 보여준다.
6. 관련 논문을 검색하려면 Auto Plan의 `Local PDF / Paper Evidence...`를 선택한다. **파일은 외부 전송되지 않는다.**

### JSON 원자 매핑 계약

- Monomer SMILES 필수 맵: **`N:1`**(자유 α-amino N), **`C:2`**(α-carboxyl C), **`O:3`**(carboxyl OH). 기타 반응 부위는 고유한 `10+` 원자번호를 사용한다.
- 반응 부위 참조: 전역에서 `residue_position:atom_map_number`(예: `2:10`)로 지정. 여러 Chain의 Monomer도 1부터 연결하여 번호를 부여한다.
- `monomers`는 단일 주쇄, `chains`는 서로 독립된 여러 주쇄/분지 Arm이다. 분지 연결 전에는 자동으로 서로 붙지 않는다.
- `steps`는 **`amide`, `disulfide`, `thioether_substitution`, `thiol_michael`, `cuaac_1_4`, `rcm`** 중 하나. 정의되지 않은 반응은 거부한다. Head-to-tail 단일 Chain은 `head_to_tail: true`로 지정한다.
- 모든 Monomer는 자유 아민과 카복실기를 갖는 **서열 조립 블록**이어야 한다. 말단 Ac/Fmoc처럼 N이 캡핑된 최종 구조를 임의로 자유 아민이라 가정하지 않는다. 캡·링커의 확장 템플릿은 별도 검증이 필요하다.

### 반응 시약과 구조 그래프의 구분

CuAAC, RCM 등에서 이론 결합을 만들 수 있다고 해서 **Cu 촉매·Ru 촉매·산화제·커플링 시약의 추천 eq, 반응 시간, 용매 또는 수득률을 정할 수는 없다.** 기존 Reaction Method Library는 실험자 검토용이며 자동으로 반응을 적용하지 않는다. 문헌 메타데이터·PDF 검색 결과도 검증된 SOP를 뜻하지 않는다.

## 검증 명령

```bash
python -m pytest -q tests/test_v9_atomic_topology_sharp.py tests/test_v9_custom_monomer_registry.py tests/test_v9_fulltext_evidence_sharp.py
python tools/validate_atomic_topology_v9.py
python main_launcher.py --self-test
python tools/verify_windows_release.py
```

**Windows 네이티브 EXE/Installer 검증:** GitHub Actions의 Windows job에서 실제 빌드 후 `tools/windows_installer_acceptance_v9.py`가 임시 CI 설치·제거를 검사한다. Linux에서 해당 스크립트는 `NOT_TESTED`를 반환한다. 실제 Windows PC 장시간 실행/사용자 데이터 보존 검증은 별도 작업이 필요하다.

## AI/ML의 검증 경계

기존 AI Excel 자동 정리, 프로세스별 학습, 그룹 검증, 안전 JSON 모델, 외부 홀드아웃 평가 코드는 보존했다. 그러나 **외부 독립 실제 합성 데이터가 제공되지 않아** 수득률·순도 모델의 실험적 정확도를 평가하거나 개선 성과를 입증하지 못했다. 템플릿과 코드를 실행하는 것만으로 예측 정확도가 확보되지 않는다.

## 코드 출처와 라이선스

- RDKit 원본: https://github.com/rdkit/rdkit — BSD-3-Clause. 그래프 및 원자 매핑 API의 공식 사용법을 참고했으며 기존 타 프로젝트 코드를 복사하지 않았다.
- RDKit 반응 문법: https://www.rdkit.org/docs/RDKit_Book.html
- scikit-learn 모델 보안: https://scikit-learn.org/stable/model_persistence.html
- Crossref 공식 API: https://www.crossref.org/documentation/retrieve-metadata/rest-api

SPPS Planner 저장소의 기존 사용자 정의 `LICENSE`는 OSI 승인 라이선스로 표시하지 않는다. RDKit의 라이선스 및 배포 의존성 고지는 유지한다.
