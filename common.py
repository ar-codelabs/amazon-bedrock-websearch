"""
공통  (두 방식이 공유)
- 입력: PM 큐레이션 목적 (자연어)
- 출력: 통일된 큐레이션 결과 스키마
- YouTube: yt-dlp 기반 NBA 공식 채널 영상 검색 (API 키 불필요)
- 포맷팅/출력 유틸
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any

NBA_CHANNEL_ID = os.environ.get("NBA_CHANNEL_ID", "UCWJ2lWNubArHWmf3FIHbfcQ")


# ---------- 입력 ----------
@dataclass
class CurationRequest:
    """PM이 입력하는 큐레이션 목적."""
    purpose: str                 # 예: "이번 주 가장 화제인 NBA 경기와 관련 영상 큐레이션"
    max_web_results: int = 5
    max_youtube_results: int = 5


# ---------- 출력 (통일 스키마) ----------
@dataclass
class WebFinding:
    title: str
    url: str
    snippet: str = ""


@dataclass
class YouTubeVideo:
    title: str
    url: str
    video_id: str
    upload_date: str = ""        # YYYYMMDD
    duration_sec: int = 0
    view_count: int = 0
    description: str = ""


@dataclass
class CurationResult:
    """두 방식이 동일하게 채우는 최종 출력."""
    approach: str                              # "gpt_pipeline" | "agentcore_agent"
    purpose: str
    summary: str = ""                          # LLM이 작성한 큐레이션 요약
    web_findings: list[WebFinding] = field(default_factory=list)
    youtube_videos: list[YouTubeVideo] = field(default_factory=list)
    elapsed_sec: float = 0.0
    notes: str = ""                            # 실행 관련 메모 (fallback 등)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


# ---------- YouTube 검색 (yt-dlp, 키 불필요) ----------
def search_nba_youtube(query: str, max_results: int = 5,
                       channel_id: str = NBA_CHANNEL_ID) -> list[YouTubeVideo]:
    """
    NBA 공식 채널 안에서 query로 영상 검색.
    yt-dlp의 채널 검색 URL(ytsearch 대신 채널 내 검색 탭)을 사용.
    """
    import yt_dlp

    # 채널 내 검색: youtube.com/channel/<id>/search?query=... 를 flat 추출
    search_url = f"https://www.youtube.com/channel/{channel_id}/search?query={query}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,      # 영상 상세는 안 받고 목록 메타만 (빠름)
        "playlistend": max_results,
        "default_search": "ytsearch",
    }

    videos: list[YouTubeVideo] = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_url, download=False)
        except Exception as e:
            print(f"[youtube] 채널 검색 실패, ytsearch 폴백: {e}")
            info = ydl.extract_info(f"ytsearch{max_results}:NBA {query}", download=False)

        entries = (info or {}).get("entries", []) or []
        for entry in entries[:max_results]:
            if not entry:
                continue
            vid = entry.get("id", "")
            videos.append(YouTubeVideo(
                title=entry.get("title", ""),
                url=entry.get("url") or f"https://www.youtube.com/watch?v={vid}",
                video_id=vid,
                upload_date=entry.get("upload_date", "") or "",
                duration_sec=int(entry.get("duration") or 0),
                view_count=int(entry.get("view_count") or 0),
                description=(entry.get("description") or "")[:200],
            ))
    return videos


# ---------- 출력 유틸 ----------
def print_result(result: CurationResult) -> None:
    print("\n" + "=" * 70)
    print(f"  방식: {result.approach}  |  소요: {result.elapsed_sec:.1f}s")
    print("=" * 70)
    print(f"\n[목적] {result.purpose}\n")
    print(f"[요약]\n{result.summary}\n")

    print(f"[웹 검색 결과] ({len(result.web_findings)}건)")
    for i, w in enumerate(result.web_findings, 1):
        print(f"  {i}. {w.title}")
        print(f"     {w.url}")
        if w.snippet:
            print(f"     {w.snippet[:100]}")

    print(f"\n[NBA 채널 영상] ({len(result.youtube_videos)}건)")
    for i, v in enumerate(result.youtube_videos, 1):
        meta = []
        if v.upload_date:
            meta.append(v.upload_date)
        if v.view_count:
            meta.append(f"{v.view_count:,}회")
        if v.duration_sec:
            meta.append(f"{v.duration_sec}s")
        meta_str = f" ({', '.join(meta)})" if meta else ""
        print(f"  {i}. {v.title}{meta_str}")
        print(f"     {v.url}")

    if result.notes:
        print(f"\n[메모] {result.notes}")
    print("=" * 70 + "\n")


# ---------- AgentCore Gateway Web Search (SigV4 직접 호출) ----------
class AgentCoreWebSearch:
    """
    AgentCore Gateway의 빌트인 Web Search Tool을 SigV4로 직접 호출하는 경량 MCP 클라이언트.
    server.py 프록시 로직을 인프로세스로 가져온 것 (stdio 대신 함수 호출).
    """

    SERVICE = "bedrock-agentcore"

    def __init__(self, gateway_url: str | None = None, region: str = "us-east-1"):
        import re as _re
        self.gateway_url = (gateway_url or os.environ["AGENTCORE_GATEWAY_URL"]).strip()
        m = _re.search(r"\.([a-z]{2}-[a-z]+-\d)\.amazonaws\.com", self.gateway_url)
        self.region = m.group(1) if m else region
        self._session_id: str | None = None
        self._rpc_id = 0

        from botocore.session import Session
        creds = Session().get_credentials()
        if creds is None:
            raise RuntimeError("AWS 자격증명을 찾을 수 없습니다.")
        self._creds = creds

    def _rpc(self, method: str, params: dict | None = None) -> dict:
        import urllib.request
        import urllib.error
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest

        self._rpc_id += 1
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": method,
            "params": params or {},
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        aws_req = AWSRequest(method="POST", url=self.gateway_url, data=body, headers=headers)
        SigV4Auth(self._creds, self.SERVICE, self.region).add_auth(aws_req)
        prepared = aws_req.prepare()

        req = urllib.request.Request(self.gateway_url, data=body, method="POST")
        for k, v in prepared.headers.items():
            req.add_header(k, v)

        try:
            resp = urllib.request.urlopen(req, timeout=60)
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self._session_id = sid
            ct = resp.headers.get("Content-Type", "")
            text = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            ct = e.headers.get("Content-Type", "")
            text = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"Gateway HTTP {e.code}: {text[:300]}")

        return self._parse(text, ct)

    @staticmethod
    def _parse(text: str, content_type: str) -> dict:
        text = (text or "").strip()
        if "text/event-stream" in content_type:
            result = None
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict) and ("result" in obj or "error" in obj):
                        result = obj
            return result or {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def initialize(self) -> None:
        self._rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "tv-sports-curation", "version": "0.1"},
        })

    def list_tools(self) -> list[dict]:
        resp = self._rpc("tools/list")
        return resp.get("result", {}).get("tools", [])

    def search(self, query: str, max_results: int = 5) -> list[WebFinding]:
        """웹 검색 실행 → WebFinding 리스트 반환."""
        tools = self.list_tools()
        tool_name = next(
            (t["name"] for t in tools if "websearch" in t["name"].lower().replace("_", "").replace("-", "")),
            "WebSearch",
        )
        resp = self._rpc("tools/call", {
            "name": tool_name,
            "arguments": {"query": query[:200], "maxResults": max_results},
        })
        return self._to_findings(resp)

    @staticmethod
    def _to_findings(resp: dict) -> list[WebFinding]:
        findings: list[WebFinding] = []
        content = resp.get("result", {}).get("content", []) or []
        for block in content:
            if block.get("type") != "text":
                continue
            raw = block.get("text", "")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                findings.append(WebFinding(title="", url="", snippet=raw[:200]))
                continue
            items = data if isinstance(data, list) else data.get("results") or data.get("items") or []
            for it in items:
                if not isinstance(it, dict):
                    continue
                findings.append(WebFinding(
                    title=it.get("title", ""),
                    url=it.get("url", "") or it.get("link", ""),
                    snippet=(it.get("snippet") or it.get("content") or it.get("text") or "")[:200],
                ))
        return findings
