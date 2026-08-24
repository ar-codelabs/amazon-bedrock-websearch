# 실행 결과 비교 — 방식 1 vs 방식 2

동일한 큐레이션 목적을 두 방식에 넣고 나란히 실행한 결과입니다.
**현재 날짜(2026-08-25) 기준 최신 검색**이 되도록 개선한 뒤의 결과입니다.

- **실행 목적(입력)**: `"이번 시즌 가장 화제인 NBA 선수와 관련 하이라이트 영상 큐레이션"`
- **실행 명령**: `python compare.py --purpose "이번 시즌 가장 화제인 NBA 선수와 관련 하이라이트 영상 큐레이션"`
- **리전**: us-east-1
- **모델**: 방식1 `openai.gpt-5.6-terra` / 방식2 `us.anthropic.claude-sonnet-4-6`
- **기준 날짜**: 2026-08-25 (UTC)
- **external_web_access**: true

---

## 요약 비교표

| 항목 | 방식 1 (GPT 파이프라인) | 방식 2 (AgentCore 에이전트) |
|---|---|---|
| 소요 시간 | 53.8초 | **33.8초** |
| 웹 검색 결과 수 | 5건 | **8건** |
| YouTube 영상 수 | 5건 | **10건** |
| 웹검색 호출 횟수 | 1회 (코드 고정) | 여러 번 (모델 자율) |
| 선정 화제 선수 | 제일런 브런슨 (닉스 우승) | 빅터 웸반야마 |
| 시즌 초점 | **2025-26 시즌** ✅ | **2025-26 시즌** ✅ |
| 날짜 필터 | 프롬프트로 기준일 명시 | 프롬프트 + 발행일 필터(최근 30일) |
| 웹검색 엔진 | Bedrock 빌트인 (Responses/mantle) | AgentCore Gateway (SigV4/MCP) |
| 오케스트레이션 | 코드가 순서 고정 | 모델이 툴 루프에서 자율 결정 |

---

## 방식 1 — GPT 파이프라인 (53.8초)

**흐름**: (현재 날짜 주입) 웹검색 1회 → 키워드 추출(`Jalen Brunson`) → NBA 유튜브 5건 → GPT 종합

**큐레이션 요약**
> 2025-26시즌 NBA 하이라이트 큐레이션의 최우선은 닉스의 53년 만의 우승을 완성한 제일런 브런슨입니다.
> 특히 파이널 5차전에서 45점을 터뜨리고 파이널 MVP를 확정한 경기 영상과, NBA 공식 채널의
> 'Jalen Brunson's Top Plays of the Knicks Championship Run'을 메인 콘텐츠로 추천합니다.
> 함께 웸반야마의 스퍼스 플레이오프·파이널 림 프로텍팅, SGA의 2년 연속 MVP급 클러치 모음,
> 쿠퍼 플래그의 올랜도전 51점 영상은 각각 차세대 스타·개인 지배력·신인 돌풍을 보여주는 보조 축으로 적합합니다.

**웹 검색 결과 (5건)**
1. Knicks' Brunson seals Finals MVP honors with 45 points in Game 5 — espn.com
2. All-NBA Playoff Awards: Which stars made our first, second teams? — espn.com
3. Victor Wembanyama betting favorite for 2026-27 NBA MVP — forbes.com
4. Thunder star Shai Gilgeous-Alexander repeats as NBA MVP — espn.com
5. Rookie Cooper Flagg has 51-point night in Mavericks loss — espn.com

**NBA 채널 영상 (5건)**
1. Jalen Brunson's Top Plays of the Knicks Championship Run 🏆🗽🔥 (119,610회)
2. Jalen Brunson Ties Michael Jordan with LEGENDARY 45-PT Finals Performance 👑 | June 13, 2026 (250,541회)
3. Jalen Brunson ERUPTS For New CAREER-HIGH 61 PTS! 🔥 | March 29, 2024 (195,327회)
4. It Gets SPOOKY Guarding Jalen Brunson 😳 | Top Handles of the 2025-26 Season (27,426회)
5. Jalen Brunson's Top 20 Moments of the 2024-25 NBA Season! (114,857회)

---

## 방식 2 — AgentCore 에이전트 (33.8초)

**흐름**: (현재 날짜 주입 + 최근 30일 발행일 필터) Claude가 웹검색을 자율 호출 →
NBA 유튜브 다중 검색 → 종합. 도구 호출 순서/횟수를 모델이 결정.

**큐레이션 요약**
> 2025-26 NBA 시즌 최고의 화제 선수는 단연 **빅터 웸반야마**로, ESPN 등 주요 매체들이 이번 시즌을
> 정의한 인물로 그를 지목했습니다. 220cm의 압도적인 피지컬에 가드급 볼 핸들링과 포스트시즌에서도
> 빛난 클러치 플레이로 전 세계 팬들의 시선을 사로잡았으며, NBA 공식 유튜브에는 "7피트가 이래도 되냐"는
> 반응을 이끌어낸 하이라이트 영상들이 폭발적인 조회수를 기록 중입니다. TV 편성 시 웸반야마의 시즌
> 하이라이트 및 포스트시즌 명장면 영상을 중심으로 구성하면 시청자 몰입도를 극대화할 수 있습니다.

**웹 검색 결과 (8건, 일부)** — 모두 최근 30일 내 발행
1. Picking the NBA moment that defined the 2025-26 season — espn.com
2. The most popular contemporary basketball players in America 2026 — yougov.com
3. Team USA Olympic stock watch: Which NBA players are rising, falling? — espn.com
4. Wemby Season 2026 (25.0 PPG / 11.5 REB / 3.1 AST, 64경기) — statmuse.com
5. Victor Wembanyama Stats, Game Log, News — heavy.com

**NBA 채널 영상 (10건, 일부)**
1. The Top Plays of the 2025-26 NBA Season | Pt.1 (203,554회)
2. Top 50 Handles of the 2025-26 NBA Season! (253,602회)
3. The TOP Plays of Week 1 | 2025-26 NBA Season (779,620회)
4. Victor Wembanyama's Season Highlights Are Simply UNREAL 🤯 | 2025-26 NBA Season (849,957회)
5. Victor Wembanyama's Most ELECTRIC Plays of the Postseason 🔥 (247,809회)
6. A 7-Footer Shouldn't Be Able to Do This 😳 | Wemby's Top Handles of the 2025-26 NBA Season (20,747회)

---

## 분석

### 1. 시점 정렬 — 개선 확인
현재 날짜 주입 후 두 방식 모두 **2025-26 시즌**으로 정렬되었습니다.
특히 방식2는 발행일 필터(최근 30일)로 웹 검색 결과가 전부 2025-26 시즌을 다룬 최신 기사
(`Picking the NBA moment that defined the 2025-26 season` 등)로 바뀌어, 시즌 혼선이 없습니다.

### 2. 선정 관점 차이
- **방식1**: 웹검색 1회 결과에서 "우승/파이널 MVP"라는 **이벤트 임팩트**에 주목 → 제일런 브런슨(닉스 우승).
- **방식2**: 여러 번 검색하며 "시즌을 정의한 인물"이라는 **매체 담론**에 주목 → 빅터 웸반야마.

둘 다 2025-26 시즌 화제 인물로 타당하며, 관점(단일 이벤트 vs 시즌 서사)이 달라 선택이 갈렸습니다.

### 3. 속도 vs 풍부함
- 방식1: 53.8초 / 웹5·영상5 — 이번 실행에선 GPT 웹검색 단계가 더 오래 걸렸습니다.
- 방식2: 33.8초 / 웹8·영상10 — 날짜 필터로 후보군이 좁혀져 오히려 빠르고 결과도 풍부했습니다.

> 소요 시간은 실행마다 편차가 큽니다(모델 응답·웹 상태 의존). 순서를 단정하기보다 경향으로 보세요.

### 4. 아키텍처 관점
- 방식2는 웹검색·YouTube를 **Claude 단일 툴 루프**로 통합하고, 발행일 필터 같은 검색 제어까지
  도구 레벨에서 걸 수 있어 Gracenote SQL 툴 등 확장에 유리합니다.
- 방식1은 빌트인 웹검색이 간편하지만 모델이 GPT로 고정되고, 날짜 제어는 프롬프트에만 의존합니다.

---

## 결론

| 우선순위 | 추천 방식 |
|---|---|
| 속도·단순함·예측가능성 | **방식 1 (파이프라인)** |
| 풍부함·자율 판단·검색 제어·확장성 | **방식 2 (에이전트)** |

- "이번 시즌/최신" 같은 상대적 표현은 **반드시 현재 날짜를 프롬프트에 주입**해야 올바르게 해석됩니다.
- 최신성이 중요한 큐레이션에서는 방식2의 **발행일 필터**가 결과 품질을 눈에 띄게 높였습니다.

> 참고: 측정값은 네트워크·모델 응답·웹 결과에 따라 실행마다 달라질 수 있습니다. 위 수치는 1회 실행 기준 스냅샷입니다.
