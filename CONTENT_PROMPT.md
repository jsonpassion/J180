# 일팔공 (JLPT) — 콘텐츠 생성 프롬프트

> **일팔공 / One80** 앱의 단어 콘텐츠 전체를 이 리포(`~/Documents/Developer/j180-content`)에 만들어 올리는 붙여넣기용 프롬프트.
> 규격 원본은 `content.config.json` · `plan/curriculum.json` · `prompts/` · `tools/`이며, 절차 상세는 [OVERNIGHT.md](OVERNIGHT.md).
> 이 문서는 **앱 구조가 바뀐 뒤(2026-09-14) 기준**으로 콘텐츠가 앱에 맞게 들어가도록 필요한 사실을 한곳에 모았다.

## 사용법

1. 터미널에서 `cd ~/Documents/Developer/j180-content && claude` 로 이 리포를 연다.
2. 아래 **붙여넣기 프롬프트** 블록 전체를 그대로 붙여넣는다. 첫 단어 `ultracode`가 멀티 에이전트 병렬 실행을 켠다.
3. 중간에 끊겨도 같은 프롬프트를 다시 붙여넣으면 된다. 이미 쓰인 권은 동결되고 `todo`에 남은 권만 이어서 쓴다.

## 앱이 이 콘텐츠를 읽는 방식

| 항목 | 내용 |
|---|---|
| 앱 | 일팔공 / One80 (JLPT, 타깃 `J180`) — 한국인 JLPT 수험생, 한국어 UI |
| 레벨 방식 | **급수 모드**(점수대 아님). 사용자가 N5–N1 중 고르고, 대시보드는 `합격 X/180`(합격선 N5 80 · N4 90 · N3 95 · N2 90 · N1 100)으로 표시 |
| 권 구성 | **N5 8권 · N4 7권 · N3 20권 · N2 20권 · N1 25권 = 80권 8,000단어**, 100단어 = 1권, 10단어 = 1챕터 |
| 무료 | 급수마다 1권(10챕터) |
| 줄 형식 | `- 표기 \| 한국어 뜻 \| 읽기(히라가나/가타카나) \| TIP \| 日本語の例文 \| 예문 번역` |
| 카드 | **앞면 = 표기만**(한자 또는 가나, 읽기 숨김 — 한자를 읽을 수 있는지가 시험 포인트), 뒷면 = 표기 + 읽기 + 뜻·TIP·예문·번역. TTS = 일본어 단어/예문 + 한국어 뜻 |
| 중복 | 트랙 전체에서 `표기+읽기` 기준 중복 금지 — 같은 한자라도 읽기가 다르면 다른 단어(上手 じょうず / うわて) |
| 배포 | `manifest.json` → `https://raw.githubusercontent.com/jsonpassion/J180/main/manifest.json` |

## 붙여넣기 프롬프트

```
ultracode. 이 리포(현재 디렉토리)는 일팔공 / One80 앱의 단어 콘텐츠 리포다. main 에 push 하면 앱에 배포된다.
아래 사실과 품질 기준을 지키며 OVERNIGHT.md 절차로 전체 단어책을 끝까지 만들고 배포하라.

[앱 구조]
- 앱 : 일팔공 / One80 (JLPT, 타깃 J180) — 한국인 JLPT 수험생, 한국어 UI
- 레벨 방식 : 급수 모드(점수대 아님). 사용자가 N5–N1 중 고르고, 대시보드는 합격 X/180(합격선 N5 80 · N4 90 · N3 95 · N2 90 · N1 100)으로 표시
- 권 구성 : N5 8권 · N4 7권 · N3 20권 · N2 20권 · N1 25권 = 80권 8,000단어, 100단어 = 1권, 10단어 = 1챕터
- 무료 : 급수마다 1권(10챕터)
- 줄 형식 : - 표기 | 한국어 뜻 | 읽기(히라가나/가타카나) | TIP | 日本語の例文 | 예문 번역
- 카드 : 앞면 = 표기만(한자 또는 가나, 읽기 숨김 — 한자를 읽을 수 있는지가 시험 포인트), 뒷면 = 표기 + 읽기 + 뜻·TIP·예문·번역. TTS = 일본어 단어/예문 + 한국어 뜻
- 중복 : 트랙 전체에서 표기+읽기 기준 중복 금지 — 같은 한자라도 읽기가 다르면 다른 단어(上手 じょうず / うわて)
- 배포 : manifest.json → https://raw.githubusercontent.com/jsonpassion/J180/main/manifest.json

[품질 기준]
- JLPT는 2010년 이후 공식 어휘 목록이 없다. 구 출제기준(4급→N5 … 1급→N1) 배정과 실제 출제 경향을 기준으로, 아래 급수에 이미 나온 단어는 위 급수에 넣지 않는다.
- 표기는 실제로 쓰이는 표기(常用 한자 표기, 보통 가나로 쓰는 말은 가나). 가나 전용 단어는 표기와 읽기가 같은 가나여도 된다. 외래어는 가타카나.
- 읽기는 장음·촉음·탁음·요음을 정확히(병원 びょういん / 미용실 びよういん 같은 함정 주의).
- 뜻은 한국어로 시험에 나오는 뜻 먼저 최대 2개, 동사는 "~하다", 자동사·타동사는 구별이 드러나게.
- TIP(한국어 45자 이내): 한국 한자어 연결(約束=약속) · 한국어와 뜻이 다른 한자어 경고 · 자타동사 쌍(開く/開ける) · 読み 함정 · 言い換え 유의어 · 용법 구별 중 가장 효과적인 한 줄.
- 예문 10–30자, 그 급수 문법 수준. 활용형 허용하되 표제어의 한자 부분은 그대로 보이게.

[절차]
1) python3 tools/plan.py clear-dummy && python3 tools/plan.py wordlist-briefs
2) 밴드마다 에이전트 1개씩 병렬: plan/briefs/wordlist-<band>.md 를 읽고 그대로 수행해 plan/wordlists/<band>.md 작성.
3) python3 tools/plan.py merge — SHORT 가 나오면 그 권의 후보만 보충하는 에이전트를 돌리고 merge 를 반복해 0 short 로 만든다.
4) python3 tools/plan.py briefs
5) plan/briefs/<band>/unit-NNN.md 하나당 에이전트 1개, 동시 최대 12개. 각 에이전트는 brief 를 그대로 수행해 자기 파일 하나만 쓰고
   python3 tools/validate_content.py --unit <band>/NNN 이 0 errors 가 될 때까지 자기 파일의 오류 줄만 고친다.
6) python3 tools/validate_content.py 전체 0 errors 가 될 때까지 python3 tools/plan.py todo 의 목록만 5)를 반복.
7) 밴드 하나가 끝날 때마다 python3 tools/build_manifest.py → git add content plan manifest.json → 커밋 → push (중간 배포 허용).

[금지]
- 표제어 선정과 배정은 반드시 `plan.py merge` 결과만 따른다. 작성 에이전트는 단어를 고르거나 바꾸지 않는다.
- 실제 기출문제·유료 교재 문장을 옮기지 않는다. 예문·TIP은 전부 새로 쓴다.
- `docs/`, `privacy.md`, `terms.md`, `README.md`는 건드리지 않는다(사이트·약관은 별도 관리).
- `tools/*.py`에 버그가 보이면 고치지 말고 멈춰서 보고한다(모든 앱 리포가 같은 도구를 공유함).
- 출시 전이므로 더미 권 삭제는 괜찮다. **출시 후에는 표제어 철자 변경·삭제 금지** — 카드 ID(`<unit id>-<표제어>`)에 학습 기록이 묶여 있다.

[완료 조건]
- python3 tools/validate_content.py 0 errors, 경고는 권당 3개 이하.
- python3 tools/plan.py todo 가 "nothing to do", status 의 written 합계 = 80권, 총 8,000단어, dummy 권 0개.
- python3 tools/build_manifest.py --check 가 up to date, push 후 raw manifest 의 version 이 로컬과 같다.
끝나면 급수(밴드)별 권 수·단어 수, 경고 수, 커밋 해시, raw manifest 버전을 보고하라.
```

## 완료 확인 (사람이 직접)

```bash
python3 tools/plan.py status
python3 tools/validate_content.py --quiet | tail -1
python3 tools/build_manifest.py --check
curl -s https://raw.githubusercontent.com/jsonpassion/J180/main/manifest.json | head -3
```
