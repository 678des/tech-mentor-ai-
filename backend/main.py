import os

from dotenv import load_dotenv  
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ai import evaluate_articles_with_gemini, generate_context_advice
from crud import *
from pydantic import BaseModel, Field
from typing import List, Literal
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


class ArticleUserStateUpdate(BaseModel):
    save_type: Literal["later", "important","done"] | None = None
    user_note: str | None = None


class UserContextUpdate(BaseModel):
    career_goal: str = ""
    current_focus: str = ""
    subjects: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    current_situation: str = ""
    projects: List[str] = Field(default_factory=list)


class ContextAdviceTheme(BaseModel):
    theme: str
    why: str
    article_angles: List[str]
    search_queries: List[str]


class ContextAdviceResponse(BaseModel):
    overview: str
    themes: List[ContextAdviceTheme]
    after_reading_choices: List[str]
    reminder: str

    
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


@app.get("/api/user-context")
def get_user_context_endpoint():
    try:
        return get_user_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー情報の取得に失敗しました: {e}")


@app.put("/api/user-context")
def save_user_context_endpoint(body: UserContextUpdate):
    try:
        return save_user_context(body.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー情報の保存に失敗しました: {e}")


@app.post("/api/user-context/advice", response_model=ContextAdviceResponse)
def get_user_context_advice_endpoint():
    try:
        user_context = get_user_context()
        return generate_context_advice(user_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"情報の見方の提案に失敗しました: {e}")


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

@app.get("/api/articles/important")
def get_important_articles_endpoint():
    try:
        articles = get_important_articles()
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"重要記事の取得に失敗しました: {e}",
        )


@app.patch("/api/articles/{article_id}/user-state")
def update_article_state_endpoint(article_id: int, body: ArticleUserStateUpdate):
    """記事の保存タイプと自分用メモを保存する。save_type=nullで保存を解除する。"""
    try:
        article = update_article_user_state(article_id, body.save_type, body.user_note)
        if article is None:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記事の保存に失敗しました: {e}")




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
        user_context = get_user_context()
        evaluated = evaluate_articles_with_gemini(unprocessed, user_context)
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
