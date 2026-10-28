from dotenv import load_dotenv  
load_dotenv()

import feedparser
from bs4 import BeautifulSoup
from typing import Any, List

from crud import get_all_urls,save_articles
from qiita import get_qiita_article_by_url

MAX_SUMMARY_LENGTH = 2000
RSS_URLS = [
    "https://zenn.dev/feed",
    "https://qiita.com/popular-items/feed",
]


def clean_summary(raw_summary: str | None) -> str:
    """Convert an RSS summary to readable text and retain a useful excerpt."""
    if not raw_summary:
        return ""
    text = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())[:MAX_SUMMARY_LENGTH]


def refresh_article_summary(article: dict[str, Any]) -> dict[str, Any]:
    """Refresh only through an official API supported for the article source."""
    article_url = article.get("url")
    if not article_url:
        raise ValueError("記事URLがありません")

    from urllib.parse import urlparse

    hostname = (urlparse(article_url).hostname or "").lower()
    if hostname in {"qiita.com", "www.qiita.com"}:
        return get_qiita_article_by_url(article_url)

    raise LookupError(
        "この記事提供元には概要更新用の公式APIを設定していないため、更新しませんでした。"
    )

def get_news():
    checked_urls = get_all_urls()
    # 3. RSSフィードのURLリスト
    candidates: List[dict[str, str]] = []
    for url in RSS_URLS:
        feed: Any = feedparser.parse(url)
        for entry in feed.entries[:25]:
            title = entry.title
            link = entry.link
            # RSS概要はフィードに含まれる範囲を活かし、最大2000文字保存する。
            summary = clean_summary(getattr(entry, 'summary', None))

            if link in checked_urls:continue
            print("タイトル",title,link,end="\n")
            candidates.append({
                "title": title,
                "url": link,
                "summary": summary
            })

    # タイトルの重複排除
    unique_candidates: List[dict[str, str]] = []
    seen_titles: set[str] = set()
    for c in candidates:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_candidates.append(c)

    print(f"✅ {len(unique_candidates)} 件の個別記事を取得しました\n")
    save_articles(unique_candidates)
    return unique_candidates
