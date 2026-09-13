# One80 Content — JLPT 어휘 콘텐츠 리포

> **One80(일팔공)** — 급수당 만점 180에서 따온 이름.
> [NINE90](https://github.com/jsonpassion/NINE90)(TOEIC 트랙)과 동일한 콘텐츠 파이프라인을 쓰는
> JLPT 트랙 리포지토리 — 앱은 manifest URL 하나로 이 리포의 콘텐츠를 통째로 동기화합니다.

**현재 상태: 규격·도구·생성 파이프라인만 존재.** 단어는 [OVERNIGHT.md](OVERNIGHT.md) 절차로 밤새 병렬 생성한다.

## 구조

```
content.config.json               ← 트랙 규격: 밴드·권 수·언어·표기 (도구가 모두 이것을 읽는다)
plan/curriculum.json              ← 밴드별 10권 테마
prompts/wordlist.md               ← 1단계: 밴드별 후보 표제어 프롬프트
prompts/unit.md                   ← 2단계: 배정된 100단어로 권 파일 쓰기 프롬프트
tools/plan.py                     ← 후보 병합·전역 중복 제거·100개 배정·brief 생성·todo
tools/validate_content.py         ← 형식·표기·중복·배정 일치 검증 (0 errors 필수)
tools/build_manifest.py           ← manifest.json 생성
content/voca/{band}/unit-NNN.md   ← 1파일 = 1권 = 100단어 (10단어 = 1챕터)
OVERNIGHT.md                      ← 밤샘 병렬 생성 런북 + 붙여넣기용 오케스트레이션 프롬프트
```

## 급수 (급수별 합격제, 급수당 180점 만점)

| band_id | 급수 | 합격선 | 권 수 | 성격 |
|---|---|---|---|---|
| `jlpt-n5` | N5 기초 | 80/180 | 8 | 생활 기초 단어 |
| `jlpt-n4` | N4 초급 | 90/180 | 7 | 일상 회화 필수 |
| `jlpt-n3` | N3 중급 | 95/180 | 20 | 2자 한자어·복합동사·외래어 |
| `jlpt-n2` | N2 중상급 | 90/180 | 20 | 뉴스·비즈니스·言い換え |
| `jlpt-n1` | N1 고급 | 100/180 | 25 | 논설·전문·用法 |

과목별 기준점: N1–N3은 언어지식·독해·청해 각 60점 중 19점, N4–N5는 언어지식·독해 120점 중 38점·청해 19점.
앱은 `score_min 0 / score_max 180`을 쓰고, 합격선은 앱의 Track.json(`passMark`)이 갖는다.

## 단어 줄 형식 — 앞면은 표기만, 읽기는 뒷면

```
- 表記 | 한국어 뜻 | よみ(가나) | TIP | 日本語の例文 | 예문 번역
```

샘플: [content/voca/jlpt-n3/unit-001.md](content/voca/jlpt-n3/unit-001.md) — 앱 확인용 더미(급수당 20단어, `dummy: true`).
본 생성 전에 `python3 tools/plan.py clear-dummy`로 지운다.

## 콘텐츠 규칙

- 유닛당 **정확히 100단어**, 10단어 = 1챕터 (앱의 회독 단위)
- **트랙 전체에서 표제어 중복 = 오류** (급수가 달라도 같은 단어는 한 번만). 같은 표기라도 읽기가 다르면 다른 단어
- 필드 안에 파이프(`|`) 금지 (구분자 전용)
- 카드 ID = `{파일 id}-{표제어 slug}` — 줄 순서와 무관하지만, **출시 후 표제어 철자 변경·삭제는 금지**
  (사용자 학습 진도가 카드 ID에 매여 있음). 추가는 새 유닛 파일로.
- `manifest.json`의 `profile.free_chapters`(기본 10 = 1권) = 밴드마다 무료로 열리는 챕터 수
  (앱이 원격 설정으로 읽음)

## 워크플로

단어 생성은 [OVERNIGHT.md](OVERNIGHT.md) 한 곳에 정리돼 있다 (후보 목록 → 전역 중복 제거·배정 → 권별 병렬 작성 → 검증).

```bash
python3 tools/plan.py status         # 진행 상황
python3 tools/validate_content.py    # 0 errors 필수
python3 tools/build_manifest.py
git add content plan manifest.json && git commit && git push
```

앱은 raw.githubusercontent.com의 manifest.json 버전 변경을 감지해 바뀐 파일만 내려받습니다
(sha256 검증 포함). raw CDN 캐시 특성상 push 후 매니페스트 반영까지 ~5분 걸릴 수 있습니다.

## 상표 고지

일본어능력시험(JLPT)은 국제교류기금과 일본국제교육지원협회가 주최하는 시험입니다. 이 리포지토리와 관련 앱은
국제교류기금·일본국제교육지원협회와 무관하며, 두 기관의 제휴·보증·승인을 받지 않았습니다. 모든 콘텐츠는 자체 제작이며
실제 기출문제를 포함하지 않습니다.

© 2026 ForgeLab
