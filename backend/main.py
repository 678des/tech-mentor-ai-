import os
from pathlib import Path
from dotenv import load_dotenv  

print("スクリプト読み込み")
load_dotenv()

import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Any, List, Dict

# CRUDモジュールのインポート
from crud import get_all_urls, save_articles


    

# 1. 構造の定義（TypeScriptの型定義と一対一になる）
class SelectedArticle(BaseModel):
    title: str
    url: str
    reason: str  # なぜ今読むべきなのか（選定理由）

class NewsResponse(BaseModel):
    mentor_message: str            # 最後のメンターメッセージ
    selected_articles: List[SelectedArticle]  # AIが選んだ3〜5件
    all_candidates_count: int      # 取得した全記事数などのメタ情報

    
app = FastAPI()

# React(Vite)からのリクエストを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Viteのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/news")
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



  






from crud import get_all_urls, save_articles, get_top_scored_articles

@app.get("/api/articles")
def get_articles_endpoint():
    """
    Supabaseに保存されているすべての記事をJSON形式でフロントエンドに返す
    """
    articles = get_top_scored_articles()
    return {
        "count": len(articles),
        "articles": articles
    }


from ai import get_unprocessed_articles, evaluate_articles_with_gemini,update_articles_in_supabase

@app.post("/api/run-ai-pipeline")
def trigger_ai_pipeline():
    """
    フロントのボタンから叩かれるエンドポイント
    """
    try:
        print("--- リクエスト検知：AI要約パイプライン実行開始 ---")
        
        # 1. 未処理の記事を取得
        unprocessed = get_unprocessed_articles()
        if not unprocessed:
            return {"status": "ok", "message": "処理対象の新着記事はありません。", "count": 0}

        # 2. まとめてGeminiに評価させる
        evaluated = evaluate_articles_with_gemini(unprocessed)
        if not evaluated:
            return {"status": "error", "message": "Geminiからの評価取得に失敗しました。"}

        # 3. Supabaseを更新
        update_articles_in_supabase(evaluated)
        
        return {
            "status": "success", 
            "message": f"{len(unprocessed)}件の記事のAI要約・スコアリングが完了しました！",
            "count": len(unprocessed)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}