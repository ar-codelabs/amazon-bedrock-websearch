"""
방식 1: GPT 파이프라인 (에이전트 아님, 순차 오케스트레이션)

  [1] GPT + Responses API + 빌트인 web_search  ->  최신 웹 정보 + 인용
  [2] 웹 결과에서 키워드 추출 -> yt-dlp로 NBA 공식 채널 영상 검색
  [3] GPT로 웹 결과 + 영상 목록을 종합해 최종 큐레이션 요약 작성

특징:
  - 웹검색은 Bedrock 서버사이드(빌트인). 툴 루프 직접 안 짬.
  - 각 단계가 독립적 -> 디버깅 쉬움.
  - 모델은 GPT로 고정 (빌트인 web_search가 GPT 전용).
"""
import os
import time

from openai import OpenAI

from common import (
    CurationRequest,
    CurationResult,
    WebFinding,
    search_nba_youtube,
    print_result,
)

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL = os.environ.get("GPT_MODEL_ID", "openai.gpt-5.6-terra")
BASE_URL = f"https://bedrock-mantle.{REGION}.api.aws/openai/v1"
EXTERNAL_WEB = os.environ.get("EXTERNAL_WEB_ACCESS", "true").lower() == "true"


def _client() -> OpenAI:
    return OpenAI(api_key=os.environ["BEDROCK_API_KEY"], base_url=BASE_URL)


def _extract_citations(resp) -> list[WebFinding]:
    findings: list[WebFinding] = []
    seen = set()
    for item in resp.output:
        if getattr(item, "type", None) != "message":
            continue
        for block in item.content:
            for ann in getattr(block, "annotations", []) or []:
                if getattr(ann, "type", None) == "url_citation":
                    if ann.url in seen:
                        continue
                    seen.add(ann.url)
                    findings.append(WebFinding(title=ann.title or "", url=ann.url))
    return findings


def run(req: CurationRequest) -> CurationResult:
    t0 = time.time()
    client = _client()
    result = CurationResult(approach="gpt_pipeline", purpose=req.purpose)

    # --- [1] 웹 검색 ---
    web_resp = client.responses.create(
        model=MODEL,
        input=(
            f"큐레이션 목적: {req.purpose}\n\n"
            f"위 목적에 맞는 최신 정보를 웹에서 찾아 핵심을 {req.max_web_results}가지로 "
            f"정리해줘. 각 항목에 날짜와 출처를 포함해."
        ),
        tools=[{"type": "web_search", "external_web_access": EXTERNAL_WEB}],
    )
    result.web_findings = _extract_citations(web_resp)[: req.max_web_results]
    web_text = web_resp.output_text

    # --- [2] 웹 결과 기반 YouTube 검색 키워드 추출 ---
    kw_resp = client.responses.create(
        model=MODEL,
        input=(
            f"다음 웹 검색 요약에서 NBA 공식 유튜브 채널 검색에 쓸 핵심 키워드 "
            f"(선수명/팀명/이벤트) 하나만 골라 딱 그 단어만 답해줘.\n\n{web_text}"
        ),
    )
    yt_query = (kw_resp.output_text or req.purpose).strip().split("\n")[0][:60]

    # --- [2b] YouTube 검색 (yt-dlp) ---
    result.youtube_videos = search_nba_youtube(yt_query, req.max_youtube_results)

    # --- [3] 최종 종합 요약 ---
    vids_brief = "\n".join(f"- {v.title} ({v.url})" for v in result.youtube_videos)
    final_resp = client.responses.create(
        model=MODEL,
        input=(
            f"큐레이션 목적: {req.purpose}\n\n"
            f"[웹 검색 요약]\n{web_text}\n\n"
            f"[NBA 공식 채널 영상 (검색어: {yt_query})]\n{vids_brief}\n\n"
            f"위 정보를 종합해 PM에게 보여줄 큐레이션 요약을 한국어로 3-4문장 작성해줘. "
            f"어떤 경기/이슈가 화제이고 어떤 영상을 추천하는지 포함해."
        ),
    )
    result.summary = final_resp.output_text
    result.notes = f"youtube_query='{yt_query}', external_web_access={EXTERNAL_WEB}"
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
