import os
from urllib.parse import urlparse

from dotenv import load_dotenv  
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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


from ai import (
    build_article_embedding_text,
    create_embedding,
    evaluate_articles_with_gemini,
    generate_context_advice,
)
from crud import *
from pydantic import BaseModel, Field
from typing import List, Literal
from rss import get_news, refresh_article_summary
from qiita import get_qiita_article_by_url, search_qiita_articles


    

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


class ArticleVectorizeResponse(BaseModel):
    processed: int
    remaining: int
    failed_ids: List[int]


class ArticleVectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class SaveArticleUrlRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class ArticleTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=2048)

    


@app.get("/api/news")
def get_news_endpoint():
    return get_news()


@app.get("/api/qiita/search")
def search_qiita_endpoint(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1, le=100),
    per_page: int = Query(default=20, ge=1, le=100),
):
    normalized_query = q.strip()
    if not normalized_query:
        raise HTTPException(status_code=422, detail="検索キーワードを入力してください")
    try:
        return search_qiita_articles(normalized_query, page, per_page)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qiita記事の検索に失敗しました: {e}")


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

@app.post("/api/articles/save-url")
def save_article_url_endpoint(body: SaveArticleUrlRequest):
    """Save a user-provided HTTPS URL to the important articles list."""
    url = body.url.strip()
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise HTTPException(status_code=422, detail="有効な http または https の記事URLを入力してください")

    title = url
    if parsed.hostname.lower() in {"qiita.com", "www.qiita.com"}:
        try:
            title = get_qiita_article_by_url(url)["title"] or url
        except Exception:
            # Saving the URL should still work if the official metadata API is unavailable.
            title = url
    try:
        article = save_article_url_as_important(url, title)
        return {"article": article}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記事URLの保存に失敗しました: {e}")


@app.patch("/api/articles/{article_id}/title")
def update_article_title_endpoint(article_id: int, body: ArticleTitleUpdate):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="タイトルを入力してください")
    try:
        article = update_article_title(article_id, title)
        if article is None:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイトルの更新に失敗しました: {e}")


@app.post("/api/articles/{article_id}/refresh-summary")
def refresh_article_summary_endpoint(article_id: int):
    """Re-fetch one article's summary from the configured RSS feeds."""
    try:
        article = get_article_by_id(article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="記事が見つかりません")

        refreshed = refresh_article_summary(article)
        updated = update_article_summary(
            article_id,
            refreshed["title"],
            refreshed["summary"],
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="記事の更新に失敗しました")
        return {"message": "記事概要を更新しました。ベクトルは再生成が必要です。", "article": updated}
    except HTTPException:
        raise
    except LookupError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RSS概要の再取得に失敗しました: {e}")


@app.post("/api/articles/vectorize-existing", response_model=ArticleVectorizeResponse)
def vectorize_existing_articles_endpoint(
    batch_size: int = Query(default=50, ge=1, le=100),
    rebuild: bool = Query(default=True),
):
    """Embed saved title + RSS summary; rebuild=true refreshes existing vectors."""
    try:
        pending = get_articles_for_embedding(rebuild=rebuild)
        if rebuild:
            pending = [article for article in pending if article.get("embedding") is not None]
        else:
            pending = [article for article in pending if article.get("embedding") is None]
        batch = pending[:batch_size]
        failed_ids: List[int] = []
        processed = 0
        for article in batch:
            try:
                text = build_article_embedding_text(article)
                if not text.strip():
                    failed_ids.append(article["id"])
                    continue
                embedding = create_embedding(text)
                save_article_embedding(article["id"], embedding)
                processed += 1
            except Exception as e:
                print(f"記事ID {article['id']} の埋め込みに失敗: {e}")
                failed_ids.append(article["id"])
        return {
            "processed": processed,
            "remaining": max(0, len(pending) - processed - len(failed_ids)),
            "failed_ids": failed_ids,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記事のベクトル化に失敗しました: {e}")


@app.post("/api/articles/vector-search")
def search_articles_by_vector_endpoint(body: ArticleVectorSearchRequest):
    """Return similar existing articles so retrieval can be inspected directly."""
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="検索文を入力してください")
    try:
        embedding = create_embedding(f"検索クエリ: {query}")
        articles = search_similar_articles(embedding, body.limit, body.threshold)
        return {"query": query, "count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ベクトル検索に失敗しました: {e}")


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
