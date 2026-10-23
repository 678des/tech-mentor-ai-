import os

from dotenv import load_dotenv  
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai import  evaluate_articles_with_gemini
from crud import get_unprocessed_articles,update_articles_in_supabase,get_top_scored_articles
from pydantic import BaseModel
from typing import List
from rss import get_news


    

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
frontend_url_env = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [url.strip() for url in frontend_url_env.split(",")]
# React(Vite)からのリクエストを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Viteのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/news")
def get_news_endpoint():
    return get_news()
  



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