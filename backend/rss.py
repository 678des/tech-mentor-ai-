from dotenv import load_dotenv  
load_dotenv()

import feedparser
from bs4 import BeautifulSoup
from typing import Any, List

from crud import get_all_urls,save_articles
from qiita import get_qiita_article_by_url

MAX_SUMMARY_LENGTH = 2000
RSS_URLS = [
    # 面接・就活関連フィード
    "https://zenn.dev/topics/%E9%9D%A2%E6%8E%A5/feed",                  # Zenn: 面接
    "https://zenn.dev/topics/%E9%9D%A2%E6%8E%A5%E5%AF%BE%E7%AD%96/feed",          # Zenn: 面接対策
    "https://zenn.dev/topics/%E5%B0%B1%E6%B4%BB/feed",                  # Zenn: 就活
    "https://zenn.dev/topics/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E5%B0%B1%E6%B4%BB/feed", # Zenn: エンジニア就活
    "https://qiita.com/tags/%E9%9D%A2%E6%8E%A5/feed",                   # Qiita: 面接
    "https://qiita.com/tags/%E9%9D%A2%E6%8E%A5%E5%AF%BE%E7%AD%96/feed",          # Qiita: 面接対策
    "https://qiita.com/tags/%E5%B0%B1%E6%B4%BB/feed",                   # Qiita: 就活
    "https://qiita.com/tags/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E5%B0%B1%E6%B4%BB/feed", # Qiita: エンジニア就活

    # 新卒・インターン・ポートフォリオ・キャリア関連フィード
    "https://zenn.dev/topics/%E6%96%B0%E5%8D%92/feed",                  # Zenn: 新卒
    "https://zenn.dev/topics/%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%BC%E3%83%B3/feed",    # Zenn: インターン
    "https://zenn.dev/topics/%E3%83%9D%E3%83%BC%E3%83%88%E3%83%95%E3%82%A9%E3%83%AA%E3%82%AA/feed", # Zenn: ポートフォリオ
    "https://zenn.dev/topics/%E3%82%AD%E3%83%A3%E3%83%AA%E3%82%A2/feed",          # Zenn: キャリア
    "https://qiita.com/tags/%E6%96%B0%E5%8D%92%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2/feed",  # Qiita: 新卒エンジニア
    "https://qiita.com/tags/%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%BC%E3%83%B3/feed",    # Qiita: インターン
    "https://qiita.com/tags/%E3%83%9D%E3%83%BC%E3%83%88%E3%83%95%E3%82%A9%E3%83%AA%E3%82%AA/feed", # Qiita: ポートフォリオ
    "https://qiita.com/tags/%E3%82%AD%E3%83%A3%E3%83%AA%E3%82%A2/feed",          # Qiita: キャリア
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
        for entry in feed.entries[:50]:
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
