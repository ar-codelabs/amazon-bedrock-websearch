# NBA 스포츠 콘텐츠 큐레이션 — 웹검색 에이전트 2가지 방식

PM이 큐레이션 목적을 자연어로 입력하면, LLM이 **최신 웹 정보 + NBA 공식 유튜브 채널 영상**을
조합해 큐레이션 결과를 만들어 줍니다. 동일한 목적을 **2가지 아키텍처**로 구현하고 비교할 수 있습니다.

| | 방식 1 — GPT 파이프라인 | 방식 2 — AgentCore 에이전트 |
|---|---|---|
| 웹검색 | Amazon Bedrock **빌트인 Web Search** (Responses API) | **AgentCore Gateway** Web Search Tool (MCP) |
| 모델 | OpenAI GPT (`openai.gpt-5.6-terra`) | Claude (`us.anthropic.claude-sonnet-4-6`) |
| YouTube | yt-dlp (NBA 공식 채널, API 키 불필요) | 동일 |
| 도구 오케스트레이션 | **코드가 순서 고정** (웹검색→유튜브→종합) | **모델이 자율 판단** (툴 루프) |
| 인프라 | 없음 (API 키만) | CloudFormation 스택 1개 |

> 2026년 8월 출시된 [Amazon Bedrock Web Search](https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-bedrock-web-access-web-search/) 기능을 사용합니다.

---

## 아키텍처

```
방식 1 (파이프라인)                          방식 2 (에이전트)
────────────────────                        ────────────────────
[GPT + Responses API]                       [Claude + Converse 툴 루프]
  빌트인 web_search  ──▶ 웹 결과                 │
        │                                    ├─ tool: web_search ──▶ AgentCore Gateway (SigV4/MCP)
        ▼                                    │                          └─▶ AWS 웹 인덱스
  키워드 추출                                  │
        │                                    ├─ tool: search_nba_youtube ──▶ yt-dlp ──▶ NBA 채널
        ▼                                    │
  yt-dlp (NBA 채널)                            ▼
        │                                    모델이 순서/횟수 자율 결정 후 종합
        ▼
  GPT 종합 요약
```

---

## 사전 준비물

| 항목 | 방식 1 | 방식 2 | 비고 |
|---|:---:|:---:|---|
| AWS 계정 + 자격증명 | ✅ | ✅ | `aws configure` 또는 AWS_PROFILE |
| 리전 `us-east-1` | ✅ | ✅ | AgentCore Web Search는 **us-east-1 전용** |
| Python 3.9+ | ✅ | ✅ | |
| Bedrock 모델 액세스 | GPT | Claude | Bedrock 콘솔에서 모델 액세스 활성화 |
| Bedrock API 키 | ✅ | — | 아래 1-3단계에서 발급 |
| `bedrock-websearch:ExternalWebAccess` 권한 | 선택 | — | 실시간 웹 검색 시 |
| `bedrock-agentcore:*` 권한 | — | ✅ | Gateway 배포/호출 |
| YouTube API 키 | ❌ | ❌ | **불필요** (yt-dlp 사용) |

---

## 설치

```bash
# 1. 저장소 클론
git clone <YOUR_REPO_URL>
cd bedrock_websearch

# 2. 가상환경 + 의존성
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 환경변수 파일 생성
cp .env.example .env               # 이후 값 채우기 (아래 단계 참고)
```

---

## 방식 1 — GPT 빌트인 웹검색 파이프라인

### 1-1. Bedrock API 키 발급

`bedrock-mantle` 엔드포인트(Responses API)는 Bedrock API 키로 인증합니다.
IAM 사용자에게 service-specific credential을 발급합니다.

```bash
aws iam create-service-specific-credential \
  --user-name <YOUR_IAM_USER> \
  --service-name bedrock.amazonaws.com
```

출력의 `ServiceCredentialSecret` 값을 `.env`의 `BEDROCK_API_KEY`에 넣습니다.

### 1-2. (선택) 실시간 웹 접근 권한

`EXTERNAL_WEB_ACCESS=true`로 실시간 공개 웹을 검색하려면 IAM 권한이 추가로 필요합니다.
(`AmazonBedrockFullAccess`에는 포함되지 않음)

```bash
aws iam put-user-policy \
  --user-name <YOUR_IAM_USER> \
  --policy-name bedrock-websearch-external \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "bedrock-websearch:ExternalWebAccess",
      "Resource": "*"
    }]
  }'
```

> 권한 없이 `true`로 두면 Fetch 단계에서 403이 납니다. 권한 부여가 어렵다면 `.env`에서
> `EXTERNAL_WEB_ACCESS=false`로 두세요 (AWS 내부 인덱스/캐시만으로도 최신 정보가 꽤 나옵니다).

### 1-3. 실행

```bash
# 웹검색이 실제로 되는지 최소 검증
python probe_websearch.py

# 방식 1 큐레이션 실행
python approach1_gpt_pipeline.py
```

---

## 방식 2 — AgentCore Gateway 에이전트

### 2-1. AgentCore 권한 부여

```bash
aws iam put-user-policy \
  --user-name <YOUR_IAM_USER> \
  --policy-name bedrock-agentcore-poc \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "bedrock-agentcore:*",
      "Resource": "*"
    }]
  }'
```

### 2-2. Gateway 배포 (CloudFormation)

Gateway + IAM 서비스 역할 + Web Search Target을 스택 하나로 생성합니다.
인바운드 인증은 `AWS_IAM`이라 Cognito/OAuth 설정이 필요 없습니다.

```bash
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name agentcore-websearch \
  --template-file agentcore/cloudformation/agentcore-websearch-gateway.yaml \
  --capabilities CAPABILITY_IAM
```

배포 후 Gateway MCP URL을 가져와 `.env`의 `AGENTCORE_GATEWAY_URL`에 넣습니다.

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name agentcore-websearch \
  --query "Stacks[0].Outputs[?OutputKey=='GatewayMcpUrl'].OutputValue" \
  --output text
```

### 2-3. 실행

```bash
python approach2_agentcore_agent.py
```

> 이 프로젝트는 Gateway를 파이썬 에이전트에서 직접 SigV4 서명해 호출합니다
> (`common.py`의 `AgentCoreWebSearch`). `agentcore/server.py`는 Claude Code 같은
> 외부 MCP 클라이언트에 웹검색을 붙이고 싶을 때 쓰는 stdio↔HTTPS 프록시로,
> 이 에이전트 실행에는 필요하지 않습니다.

---

## 두 방식 비교 실행

동일한 목적을 두 방식에 넣고 결과/소요시간을 나란히 비교합니다.

```bash
# 기본 목적으로 두 방식 모두 실행
python compare.py

# 목적 직접 지정
python compare.py --purpose "르브론 제임스 최근 활약과 관련 영상 큐레이션"

# 한 방식만
python compare.py --only 1
python compare.py --only 2
```

출력 예시 (요약):

```
항목                    방식1 (파이프라인)        방식2 (에이전트)
──────────────────────────────────────────────────────────
소요 시간(s)            28.7                    9.6
웹 검색 결과 수          4                       5
YouTube 영상 수         5                       5
웹검색 엔진              GPT 빌트인               AgentCore Gateway
도구 오케스트레이션       코드 고정 순서            모델 자율(툴루프)
```

---

## 파일 구조

```
bedrock_websearch/
├── README.md                          # 이 문서
├── requirements.txt                   # 의존성
├── .env.example                       # 환경변수 템플릿 (.env로 복사해 사용)
├── common.py                          # 공통: 입출력 스키마 + YouTube(yt-dlp) + AgentCore 웹검색 클라이언트
├── approach1_gpt_pipeline.py          # 방식 1: GPT 빌트인 웹검색 파이프라인
├── approach2_agentcore_agent.py       # 방식 2: Claude 툴 루프 에이전트
├── compare.py                         # 두 방식 비교 실행기
├── probe_websearch.py                 # GPT 웹검색 최소 검증 스크립트
└── agentcore/
    ├── server.py                      # (참고) stdio↔SigV4 MCP 프록시 — 외부 MCP 클라이언트용
    └── cloudformation/
        └── agentcore-websearch-gateway.yaml   # Gateway 스택 템플릿
```

---

## 정리 (리소스 삭제)

테스트 후 생성한 AWS 리소스를 정리합니다.

```bash
# CloudFormation 스택 (Gateway + IAM Role + Target)
aws cloudformation delete-stack --region us-east-1 --stack-name agentcore-websearch

# IAM 인라인 정책
aws iam delete-user-policy --user-name <YOUR_IAM_USER> --policy-name bedrock-websearch-external
aws iam delete-user-policy --user-name <YOUR_IAM_USER> --policy-name bedrock-agentcore-poc

# Bedrock API 키 (service-specific credential)
aws iam list-service-specific-credentials --user-name <YOUR_IAM_USER> --service-name bedrock.amazonaws.com
aws iam delete-service-specific-credential --user-name <YOUR_IAM_USER> --service-specific-credential-id <CREDENTIAL_ID>
```


---

## 참고

- [Amazon Bedrock Web Search 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/web-search.html)
- [AgentCore Gateway Web Search Tool 문서](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connector-web-search-tool.html)
- Gateway 프록시 원본 샘플: [aws-samples/sample-aws-kr-enterprise](https://github.com/aws-samples/sample-aws-kr-enterprise/tree/main/developer-tools/agentcore-websearch-mcp)
