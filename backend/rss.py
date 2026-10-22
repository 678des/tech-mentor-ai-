from dotenv import load_dotenv  
load_dotenv()

import feedparser
from typing import Any, List

from crud import get_all_urls,save_articles

def get_news():
    
    checked_urls = get_all_urls()
    # 3. RSSフィードのURLリスト
    rss_urls = [
    "https://zenn.dev/feed",                  # Zenn（技術トレンド）
    "https://qiita.com/popular-items/feed",     # Qiita（人気記事）
    ]
    candidates: List[dict[str, str]] = []
    for url in rss_urls:
        feed: Any = feedparser.parse(url)
        for entry in feed.entries[:25]:
            title = entry.title
            link = entry.link
            # 概要を取得（HTMLタグ除去や長さ調整）
            summary = getattr(entry, 'summary', '概要なし')

            if link in checked_urls:continue
            print("タイトル",title,link,end="\n")
            candidates.append({
                "title": title,
                "url": link,
                "summary": summary[:200]  # 冒頭200文字程度
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
