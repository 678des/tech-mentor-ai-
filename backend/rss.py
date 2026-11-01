import os
from dotenv import load_dotenv  
load_dotenv()

import feedparser
from bs4 import BeautifulSoup
from typing import Any, List

from crud import get_all_urls, save_articles, vectorize_unembedded_articles

MAX_SUMMARY_LENGTH = 2000

RSS_URLS = [
    # --- 1. 企業・採用担当者の悩み（エンジニア採用・新卒採用・採用課題） ---
    # Zenn
    "https://zenn.dev/topics/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E6%8E%A1%E7%94%A8/feed", # Zenn: エンジニア採用
    "https://zenn.dev/topics/%E6%96%B0%E5%8D%92%E6%8E%A1%E7%94%A8/feed",         # Zenn: 新卒採用
    "https://zenn.dev/topics/%E6%8E%A1%E7%94%A8/feed",                         # Zenn: 採用
    # Qiita
    "https://qiita.com/tags/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E6%8E%A1%E7%94%A8/feed", # Qiita: エンジニア採用
    "https://qiita.com/tags/%E6%96%B0%E5%8D%92%E6%8E%A1%E7%94%A8/feed",         # Qiita: 新卒採用
    # note (生々しい採用の悩み・中小企業の実情・採用担当の本音)
    "https://note.com/hashtag/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E6%8E%A1%E7%94%A8/rss", # note: エンジニア採用
    "https://note.com/hashtag/%E6%96%B0%E5%8D%92%E6%8E%A1%E7%94%A8/rss",         # note: 新卒採用
    "https://note.com/hashtag/%E6%8E%A1%E7%94%A8%E3%81%AE%E6%82%A9%E3%81%BF/rss", # note: 採用の悩み
    "https://note.com/hashtag/%E6%8E%A1%E7%94%A8%E6%8B%85%E5%BD%93/rss",         # note: 採用担当
    "https://note.com/hashtag/%E4%B8%AD%E5%B0%8F%E4%BC%81%E6%A5%AD%E6%8E%A1%E7%94%A8/rss",     # note: 中小企業採用

    # --- 2. 新卒エンジニア育成・現場受け入れ・オンボーディングの悩み ---
    # Zenn
    "https://zenn.dev/topics/%E6%96%B0%E5%8D%92%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2/feed", # Zenn: 新卒エンジニア
    "https://zenn.dev/topics/%E6%96%B0%E5%8D%92%E7%A0%94%E4%BF%AE/feed",         # Zenn: 新卒研修
    "https://zenn.dev/topics/%E3%82%AA%E3%83%B3%E3%83%9C%E3%83%BC%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0/feed", # Zenn: オンボーディング
    # Qiita
    "https://qiita.com/tags/%E6%96%B0%E5%8D%92%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2/feed",  # Qiita: 新卒エンジニア
    "https://qiita.com/tags/%E6%96%B0%E5%8D%92%E7%A0%94%E4%BF%AE/feed",         # Qiita: 新卒研修
    # note
    "https://note.com/hashtag/%E6%96%B0%E5%8D%92%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2/rss", # note: 新卒エンジニア

    # --- 3. IT・エンジニア就活生側の悩み・リアルな声 ---
    # Zenn / Qiita
    "https://zenn.dev/topics/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E5%B0%B1%E6%B4%BB/feed", # Zenn: エンジニア就活
    "https://qiita.com/tags/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E5%B0%B1%E6%B4%BB/feed", # Qiita: エンジニア就活
    # note
    "https://note.com/hashtag/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E5%B0%B1%E6%B4%BB/rss", # note: エンジニア就活
    "https://note.com/hashtag/IT%E5%B0%B1%E6%B4%BB/rss",                         # note: IT就活
    "https://note.com/hashtag/%E5%B0%B1%E6%B4%BB%E3%81%AE%E6%82%A9%E3%81%BF/rss", # note: 就活の悩み

    # --- 4. はてなブックマーク（IT×採用・業界議論の最新記事） ---
    "https://b.hatena.ne.jp/q/%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2%E6%8E%A1%E7%94%A8?sort=recent&mode=rss", # はてブ: エンジニア採用
    "https://b.hatena.ne.jp/q/IT%20%E6%96%B0%E5%8D%92%E6%8E%A1%E7%94%A8?sort=recent&mode=rss", # はてブ: IT 新卒採用
]


def clean_summary(raw_summary: str | None) -> str:
    """Convert an RSS summary to readable text and retain a useful excerpt."""
    if not raw_summary:
        return ""
    text = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())[:MAX_SUMMARY_LENGTH]


def get_news(auto_vectorize: bool = True) -> List[dict[str, str]]:
    checked_urls = get_all_urls()
    candidates: List[dict[str, str]] = []
    for url in RSS_URLS:
        feed: Any = feedparser.parse(url)
        for entry in feed.entries[:50]:
            title = entry.title
            link = entry.link
            summary = clean_summary(getattr(entry, 'summary', None))

            if link in checked_urls:
                continue
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
    if unique_candidates:
        save_articles(unique_candidates)

    # RAG用に自動ベクトル化を実行
    if auto_vectorize:
        vectorize_unembedded_articles(batch_size=100)

    return unique_candidates
