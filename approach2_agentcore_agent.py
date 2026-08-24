"""
방식 2: AgentCore 에이전트 (진짜 툴 루프)

  Claude(Bedrock Converse) 가 아래 두 도구를 스스로 판단해 호출:
    - web_search        : AgentCore Gateway 빌트인 Web Search Tool (SigV4/MCP)
    - search_nba_youtube: NBA 공식 유튜브 채널 영상 검색 (yt-dlp)

  1번(파이프라인)과 달리, 도구 호출 순서/횟수를 코드가 정하지 않고
  모델이 대화 루프 안에서 동적으로 결정한다. -> "에이전트"

특징:
  - 웹검색 + YouTube 가 동일 모델(Claude)의 단일 툴 루프에 통합됨.
  - AgentCore Gateway 로 웹검색이 AWS 경계 내에서 처리됨.
  - requirement.md 가 그리던 "AgentCore Gateway 도구 통합" 그림에 부합.
"""
import os
import time

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from common import (
    CurationRequest,
    CurationResult,
    WebFinding,
    YouTubeVideo,
    AgentCoreWebSearch,
    search_nba_youtube,
    print_result,
)

REGION = os.environ.get("AWS_REGION", "us-east-1")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL_ID", "us.anthropic.claude-sonnet-4-6")

SYSTEM_PROMPT = """당신은 TV Sports 콘텐츠 큐레이션 전문가입니다.
PM이 준 큐레이션 목적에 맞춰, 최신 웹 정보와 NBA 공식 유튜브 채널 영상을 조합해
큐레이션 결과를 만듭니다.

사용 가능한 도구:
- web_search: 최신 웹 정보(경기 결과, 화제, 뉴스) 검색
- search_nba_youtube: NBA 공식 유튜브 채널에서 관련 영상 검색

작업 순서 권장:
1. web_search로 목적에 맞는 최신 화제/경기/선수를 파악한다.
2. 파악한 핵심 키워드(선수명/팀명)로 search_nba_youtube를 호출해 영상을 찾는다.
3. 종합해서 PM에게 보여줄 큐레이션 요약을 한국어 3-4문장으로 작성한다.

반드시 두 도구를 모두 활용하고, 마지막엔 요약 텍스트로 답하라."""


def run(req: CurationRequest) -> CurationResult:
    t0 = time.time()
    result = CurationResult(approach="agentcore_agent", purpose=req.purpose)

    # 웹검색 클라이언트 (툴 내부에서 결과를 result에도 적재)
    ws_client = AgentCoreWebSearch()
    ws_client.initialize()

    # --- 도구 정의 ---
    @tool
    def web_search(query: str) -> str:
        """최신 웹 정보를 검색한다. 경기 결과, 화제 뉴스, 최근 이벤트 등에 사용."""
        findings = ws_client.search(query, max_results=req.max_web_results)
        for f in findings:
            if f.url and f.url not in {x.url for x in result.web_findings}:
                result.web_findings.append(f)
        return "\n".join(f"- {f.title}: {f.url}" for f in findings) or "결과 없음"

    @tool
    def search_nba_youtube(query: str) -> str:
        """NBA 공식 유튜브 채널에서 영상을 검색한다. 선수명/팀명/이벤트로 검색."""
        from common import search_nba_youtube as _yt
        vids = _yt(query, max_results=req.max_youtube_results)
        for v in vids:
            if v.video_id and v.video_id not in {x.video_id for x in result.youtube_videos}:
                result.youtube_videos.append(v)
        return "\n".join(f"- {v.title} ({v.url})" for v in vids) or "결과 없음"

    tools = [web_search, search_nba_youtube]
    tools_by_name = {t.name: t for t in tools}

    llm = ChatBedrockConverse(model=CLAUDE_MODEL, region_name=REGION, temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # --- 툴 루프 ---
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"큐레이션 목적: {req.purpose}"),
    ]

    max_turns = 8
    for _ in range(max_turns):
        ai = llm_with_tools.invoke(messages)
        messages.append(ai)

        if not ai.tool_calls:
            result.summary = ai.text() if hasattr(ai, "text") else str(ai.content)
            break

        for tc in ai.tool_calls:
            fn = tools_by_name[tc["name"]]
            out = fn.invoke(tc["args"])
            messages.append(ToolMessage(content=out, tool_call_id=tc["id"]))

    result.notes = f"tool_turns 사용, model={CLAUDE_MODEL}"
    result.elapsed_sec = time.time() - t0
    return result


if __name__ == "__main__":
    request = CurationRequest(
        purpose="이번 시즌 가장 화제인 NBA 선수와 관련 하이라이트 영상 큐레이션",
        max_web_results=5,
        max_youtube_results=5,
    )
    res = run(request)
    print_result(res)
