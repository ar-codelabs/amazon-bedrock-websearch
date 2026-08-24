# 실행 결과 비교 — 방식 1 vs 방식 2

동일한 큐레이션 목적을 두 방식에 넣고 나란히 실행한 결과입니다.

- **실행 목적(입력)**: `"이번 시즌 가장 화제인 NBA 선수와 관련 하이라이트 영상 큐레이션"`
- **실행 명령**: `python compare.py --purpose "이번 시즌 가장 화제인 NBA 선수와 관련 하이라이트 영상 큐레이션"`
- **리전**: us-east-1
- **모델**: 방식1 `openai.gpt-5.6-terra` / 방식2 `us.anthropic.claude-sonnet-4-6`
- **external_web_access**: true

---

## 요약 비교표

| 항목 | 방식 1 (GPT 파이프라인) | 방식 2 (AgentCore 에이전트) |
|---|---|---|
| 소요 시간 | **31.3초** | 48.1초 |
| 웹 검색 결과 수 | 5건 | **22건** |
| YouTube 영상 수 | 5건 | **17건** |
| 웹검색 호출 횟수 | 1회 (코드 고정) | 여러 번 (모델 자율) |
| 선정 화제 선수 | 빅터 웸반야마 | 샤이 길저스-알렉산더(SGA), 요키치 서브 |
| 시즌 초점 | 2025-26 시즌 | 2024-25 시즌 |
| 웹검색 엔진 | Bedrock 빌트인 (Responses/mantle) | AgentCore Gateway (SigV4/MCP) |
| 오케스트레이션 | 코드가 순서 고정 | 모델이 툴 루프에서 자율 결정 |

---

## 방식 1 — GPT 파이프라인 (31.3초)

**흐름**: 웹검색 1회 → 키워드 추출(`Victor Wembanyama`) → NBA 유튜브 5건 → GPT 종합

**큐레이션 요약**
> 이번 시즌 NBA 화제의 중심은 첫 만장일치 DPOY, 올-NBA 퍼스트팀, 서부 파이널 MVP로 스퍼스를
> 파이널까지 이끈 빅터 웸반야마다. 큐레이션의 첫 영상은 레이커스전 40점·12리바운드 하이라이트로
> 공격 완성도와 압도적인 신체 능력을 보여주고, 이어 서부 파이널 OKC전 6·7차전 클립으로 탈락 위기와
> 원정 7차전 승리의 서사를 담는 구성이 좋다. 파이널 3차전 뉴욕전 32점·8리바운드·6어시스트·3블록
> 영상은 빅맨의 득점·패싱·림 보호를 모두 보여주는 대표 롱폼으로 추천한다.

**웹 검색 결과 (5건)**
1. Victor Wembanyama's unanimous NBA Defensive Player of the Year should be first of many — cbssports.com
2. SGA, Jokic, Wembanyama, Doncic, Cunningham make 1st-team All-NBA — espn.com
3. Victor Wembanyama betting favorite for 2026-27 NBA MVP — forbes.com
4. Spurs star hits stats milestone vs. Lakers — usatoday.com
5. Spurs 118-91 Thunder (May 28, 2026) Game Recap — espn.com

**NBA 채널 영상 (5건)**
1. Victor Wembanyama's Top 10 Rookie Season Plays 👀 (611,137회)
2. Victor Wembanyama's Most INSANE Career Plays! (698,977회)
3. Wemby arrives for his first-ever #NBAParis game! 🇫🇷 (1,521,622회)
4. This Russ & Wemby exchange is absolutely hilarious 😂 (3,039,272회)
5. Only Wemby 🤯 39 PTS, 15 REB & 5 BLK on 72% Shooting in Historic Playoff MASTERPIECE! (399,641회)

---

## 방식 2 — AgentCore 에이전트 (48.1초)

**흐름**: Claude가 웹검색을 여러 번 자율 호출(SGA·요키치·웸반야마 후보 탐색 → 22건) →
NBA 유튜브 다중 검색(17건) → 종합. 도구 호출 순서/횟수를 코드가 아닌 모델이 결정.

**큐레이션 요약**
> 2024-25 NBA 시즌의 최대 화제 선수는 OKC 썬더의 **샤이 길저스-알렉산더(SGA)**로, 니콜라 요키치와의
> 치열한 MVP 경쟁을 제치고 정규시즌 MVP와 파이널 MVP를 동시에 석권하며 시즌 최고의 주인공으로
> 떠올랐습니다. 특히 요키치가 60점 트리플더블이라는 역사적 기록을 세우는 상황에서도 팀을 우승으로
> 이끈 리더십이 높은 평가를 받았습니다. NBA 공식 유튜브에는 SGA의 MVP 수상 영상, 아이소 플레이
> 하이라이트, 파이널 활약 영상 등 시청자 몰입도 높은 콘텐츠가 다수 확보되어 있어 TV 편성 큐레이션에
> 즉시 활용 가능합니다. 요키치의 역대급 60점 트리플더블 영상도 함께 편성하면 이번 시즌의 극적인
> MVP 레이스 스토리를 입체적으로 전달할 수 있습니다.

**웹 검색 결과 (22건, 일부)**
- Shai Gilgeous-Alexander wins NBA MVP over Nikola Jokić — sports.yahoo.com
- NBA Finals 2025: SGA's legacy after Thunder's historic title run — espn.com
- Thunder's Shai Gilgeous-Alexander wins NBA MVP; Nikola Jokic 2nd — espn.com
- 2024-25 NBA Awards Voting — basketball-reference.com
- Victor Wembanyama / Nikola Jokić 관련 다수 (위키/ESPN 등)

**NBA 채널 영상 (17건, 일부)**
1. The Top 100 Plays of the 2024-25 NBA Season (1,078,969회)
2. Nikola Jokić's HISTORIC 60-PT TRIPLE-DOUBLE vs Timberwolves (953,765회)
3. Shai Gilgeous-Alexander Wins The 2024-25 Kia NBA MVP (143,757회)
4. SGA Iso Moments That Will Make You Say WOW 👀 (853,409회)
5. Shai Gilgeous-Alexander Is The 2025 NBA Finals MVP 🏆 (83,392회)
6. SGA's BEST PLAYS of the 2025 NBA Playoffs! (152,893회)

---

## 분석

### 1. 탐색 깊이
- **방식1**은 웹검색 1회 결과에서 키워드 하나만 뽑아 좁게 파고듭니다. 빠르고 간결하지만 후보 비교는 약합니다.
- **방식2**는 여러 후보(SGA·요키치·웸반야마)를 자율적으로 검색해 폭넓게 탐색합니다. 더 입체적인 스토리를 만들지만 결과량이 많아 후처리(개수 제한·중복 정리)가 필요합니다.

### 2. 속도 vs 풍부함
- 방식1: 31.3초 / 웹5·영상5 — **단발성 배너**처럼 빠른 산출에 유리
- 방식2: 48.1초 / 웹22·영상17 — **깊이 있는 Row 큐레이션**에 유리, 대신 느림

### 3. "이번 시즌" 해석 차이
동일 입력인데 방식1은 2025-26 시즌(웸반야마), 방식2는 2024-25 시즌(SGA)에 초점을 뒀습니다.
"이번 시즌"이 모호해 모델이 다르게 해석한 결과로, 프롬프트에 시즌을 명시하면 정렬됩니다.

### 4. 아키텍처 관점
- 방식2는 웹검색·YouTube를 **Claude 단일 툴 루프**로 통합 → Gracenote SQL 툴 등 추가 확장이 자연스럽습니다.
  requirement.md가 그리던 "AgentCore Gateway 도구 통합" 방향과 부합합니다.
- 방식1은 웹검색 모델이 GPT로 고정되는 제약이 있습니다.

---

## 결론

| 우선순위 | 추천 방식 |
|---|---|
| 속도·단순함·예측가능성 | **방식 1 (파이프라인)** |
| 풍부함·자율 판단·확장성 | **방식 2 (에이전트)** |

> 참고: 측정값은 네트워크·모델 응답·웹 결과에 따라 실행마다 달라질 수 있습니다.
> 위 수치는 1회 실행 기준 스냅샷입니다.
