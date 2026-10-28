import os
import re
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException


QIITA_ITEMS_API = "https://qiita.com/api/v2/items"
MAX_SUMMARY_LENGTH = 2000


def get_qiita_article_by_url(article_url: str) -> dict[str, Any]:
    """Fetch an article through Qiita's fixed official API endpoint."""
    parsed_url = urlparse(article_url)
    if parsed_url.scheme != "https" or parsed_url.hostname not in {"qiita.com", "www.qiita.com"}:
        raise ValueError("Qiita記事URLではありません")

    match = re.fullmatch(r"/[^/]+/items/([0-9a-fA-F]+)", parsed_url.path)
    if not match:
        raise ValueError("Qiita記事URLから記事IDを読み取れません")
    item_id = match.group(1)

    headers = {
        "Accept": "application/json",
        "User-Agent": "TechMentorAI/0.1 (personal learning project)",
    }
    access_token = os.getenv("QIITA_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.get(
            f"{QIITA_ITEMS_API}/{item_id}",
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RuntimeError("Qiita APIに接続できませんでした") from exc

    if response.status_code == 404:
        raise LookupError("Qiita上で記事が見つかりませんでした")
    if response.status_code == 429:
        raise RuntimeError("Qiita APIの利用上限に達しました。時間をおいて再試行してください")
    if not response.ok:
        raise RuntimeError(f"Qiita APIからHTTP {response.status_code}が返されました")

    try:
        item = response.json()
    except ValueError as exc:
        raise RuntimeError("Qiita APIの応答を読み取れませんでした") from exc

    body = item.get("body", "")
    summary = " ".join(BeautifulSoup(body, "html.parser").get_text(" ", strip=True).split())
    return {
        "title": item.get("title", "タイトルなし"),
        "summary": summary[:MAX_SUMMARY_LENGTH],
        "url": item.get("url", article_url),
        "source": "qiita_api",
    }


def search_qiita_articles(query: str, page: int, per_page: int) -> dict[str, Any]:
    """Qiita公式APIから記事の検索結果に必要なメタデータだけ取得する。"""
    headers = {
        "Accept": "application/json",
        "User-Agent": "TechMentorAI/0.1 (personal learning project)",
    }
    access_token = os.getenv("QIITA_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.get(
            QIITA_ITEMS_API,
            params={"query": query, "page": page, "per_page": per_page},
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Qiita APIに接続できませんでした") from exc

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        headers = {"Retry-After": retry_after} if retry_after else None
        raise HTTPException(
            status_code=429,
            detail="Qiita APIの利用上限に達しました。時間をおいて再度お試しください。",
            headers=headers,
        )
    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=f"Qiita APIからエラーが返されました（HTTP {response.status_code}）",
        )

    try:
        items = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Qiita APIの応答を読み取れませんでした") from exc

    articles = [
        {
            "id": item.get("id"),
            "title": item.get("title", "タイトルなし"),
            "url": item.get("url"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "tags": [tag.get("name", "") for tag in item.get("tags", [])],
            "author": (item.get("user") or {}).get("id", ""),
            "likes_count": item.get("likes_count", 0),
        }
        for item in items
    ]
    total_count = response.headers.get("Total-Count")

    return {
        "articles": articles,
        "page": page,
        "per_page": per_page,
        "total_count": int(total_count) if total_count and total_count.isdigit() else None,
    }
