from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

from src.config import YOUTUBE_CACHE_FILE, ensure_data_dir, get_youtube_api_key
from src.schemas import VideoResult

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
CACHE_TTL_SECONDS = 24 * 60 * 60


class YouTubeSearchError(RuntimeError):
    pass


def _cache_key(query: str, max_results: int, relevance_language: str, region_code: str) -> str:
    raw = f"{query}|{max_results}|{relevance_language}|{region_code}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_cache(path: Path = YOUTUBE_CACHE_FILE) -> dict[str, Any]:
    ensure_data_dir()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_cache(cache: dict[str, Any], path: Path = YOUTUBE_CACHE_FILE) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def search_youtube_videos(
    query: str,
    max_results: int = 5,
    relevance_language: str = "ko",
    region_code: str = "KR",
) -> list[VideoResult]:
    """Search YouTube with official YouTube Data API.

    This function does not download videos, extract audio, or scrape captions.
    """
    query = query.strip()
    if not query:
        return []

    api_key = get_youtube_api_key()
    if not api_key:
        raise YouTubeSearchError("YOUTUBE_API_KEY가 없습니다. .streamlit/secrets.toml 또는 환경변수에 설정하세요.")

    max_results = max(1, min(int(max_results), 10))
    key = _cache_key(query, max_results, relevance_language, region_code)
    cache = _read_cache()
    cached = cache.get(key)
    now = time.time()

    if cached and now - cached.get("created_at", 0) < CACHE_TTL_SECONDS:
        return [VideoResult.from_dict(item) for item in cached.get("items", [])]

    params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": relevance_language,
        "regionCode": region_code,
        "safeSearch": "strict",
    }

    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise YouTubeSearchError(f"YouTube 검색 중 오류가 발생했습니다: {exc}") from exc

    payload = response.json()
    results: list[VideoResult] = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        thumbnails = snippet.get("thumbnails", {})
        thumb = thumbnails.get("medium") or thumbnails.get("default") or thumbnails.get("high") or {}
        results.append(
            VideoResult(
                video_id=video_id,
                title=snippet.get("title", ""),
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                description=snippet.get("description", ""),
                thumbnail_url=thumb.get("url", ""),
                youtube_url=f"https://www.youtube.com/watch?v={video_id}",
            )
        )

    cache[key] = {
        "created_at": now,
        "query": query,
        "items": [item.to_dict() for item in results],
    }
    _write_cache(cache)
    return results
