import os
from typing import List, Dict, Any, Literal
from urllib.parse import urlparse

from dotenv import load_dotenv  
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai import (
    build_article_embedding_text,
    create_embedding,
    generate_rag_answer,
)
from crud import (
    get_articles,
    get_important_articles,
    save_article_url_as_important,
    update_article_title,
    update_article_user_state,
    get_articles_for_embedding,
    save_article_embedding,
    search_similar_articles,
    vectorize_unembedded_articles,
    save_articles,
    save_user_context,
    get_user_context,
    get_articles
)
from rss import get_news
from qiita import get_qiita_article_by_url, search_qiita_articles

app = FastAPI(title="IT News & RAG Research API")

frontend_url_env = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [url.strip() for url in frontend_url_env.split(",") if url.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- リクエスト/レスポンスモデル ---

class ArticleUserStateUpdate(BaseModel):
    save_type: Literal["later", "important", "done"] | None = None
    user_note: str | None = None


class SaveArticleUrlRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class ArticleTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=2048)


class ArticleVectorizeResponse(BaseModel):
    processed: int
    remaining: int
    failed_ids: List[int]


class ArticleVectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=8, ge=1, le=30)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class RagQueryResponse(BaseModel):
    query: str
    answer: str
    key_insights: List[str]
    referenced_articles: List[Dict[str, Any]]

class UserContextResponse(BaseModel):
    career_goal:str
    current_focus:str
    subjects:List[str]
    interests:List[str]
    current_situation:str
    projects:List[str]
# --- エンドポイント ---

@app.get("/api/news")
def get_news_endpoint():
    """RSS記事を取得し、未ベクトル化記事を自動インデックス化する"""
    return get_news(auto_vectorize=True)


@app.post("/api/fetch-rss")
def fetch_rss_endpoint():
    """手動でRSS記事を取得し、自動ベクトル化を実行するエンドポイント"""
    try:
        articles = get_news(auto_vectorize=True)
        return {
            "status": "success",
            "message": f"{len(articles)}件の新着記事を取得し、自動ベクトル化を行いました！",
            "count": len(articles),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RSS取得に失敗しました: {e}")


@app.post("/api/run-pipeline")
def run_pipeline_endpoint():
    """
    RAGパイプライン（RSS新着取得 + 自動ベクトル化）を実行する
    """
    try:
        articles = get_news(auto_vectorize=False)
        vec_result = vectorize_unembedded_articles(batch_size=100)
        return {
            "status": "success",
            "message": f"RSS取得（{len(articles)}件）と未インデックス記事のベクトル化（{vec_result['processed']}件）が完了しました！",
            "rss_count": len(articles),
            "vectorized_count": vec_result["processed"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"パイプライン実行に失敗しました: {e}")


@app.get("/api/articles")
def get_articles_endpoint(
    limit: int = Query(default=100, ge=1, le=200),
    unhandled_only: bool = Query(default=True),
):
    """
    未処理（save_typeが未設定）の記事を最新順で最大100件返す
    """
    articles = get_articles(limit=limit, unhandled_only=unhandled_only)
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
        raise HTTPException(status_code=500, detail=f"重要記事の取得に失敗しました: {e}")


@app.post("/api/articles/save-url")
def save_article_url_endpoint(body: SaveArticleUrlRequest):
    """ユーザーが入力したURLを保存記事に追加する"""
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
            title = url
    try:
        article = save_article_url_as_important(url, title)
        # 保存時に自動でベクトル化を試行
        try:
            embed_text = build_article_embedding_text(article)
            if embed_text.strip():
                save_article_embedding(article["id"], create_embedding(embed_text))
        except Exception as embed_err:
            print(f"個別URL保存時のベクトル化エラー（続行）: {embed_err}")
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


@app.patch("/api/articles/{article_id}/user-state")
def update_article_state_endpoint(article_id: int, body: ArticleUserStateUpdate):
    """記事の保存タイプと自分用メモを保存する。"""
    try:
        article = update_article_user_state(article_id, body.save_type, body.user_note)
        if article is None:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記事の保存に失敗しました: {e}")


@app.post("/api/articles/vectorize-existing", response_model=ArticleVectorizeResponse)
def vectorize_existing_articles_endpoint(
    batch_size: int = Query(default=50, ge=1, le=100),
    rebuild: bool = Query(default=False),
):
    """未ベクトル化記事のEmbedding生成（rebuild=trueで全件再生成）"""
    try:
        pending = get_articles_for_embedding(rebuild=rebuild)
        batch = pending[:batch_size]
        failed_ids: List[int] = []
        processed = 0

        for article in batch:
            article_id = article["id"]
            try:
                embed_text = build_article_embedding_text(article)
                if not embed_text.strip():
                    continue
                embedding = create_embedding(embed_text)
                save_article_embedding(article_id, embedding)
                processed += 1
            except Exception as e:
                print(f"Embedding error for article {article_id}: {e}")
                failed_ids.append(article_id)

        remaining = max(0, len(pending) - len(batch))
        return {
            "processed": processed,
            "remaining": remaining,
            "failed_ids": failed_ids,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記事のベクトル化に失敗しました: {e}")


@app.post("/api/articles/vector-search")
def search_articles_by_vector_endpoint(body: ArticleVectorSearchRequest):
    """ベクトル類似度検索（記事の類似度スコアと一覧を直接取得）"""
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="検索文を入力してください")
    try:
        embedding = create_embedding(f"検索クエリ: {query}")
        articles = search_similar_articles(embedding, body.limit, body.threshold)
        return {"query": query, "count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ベクトル検索に失敗しました: {e}")


@app.post("/api/rag/ask", response_model=RagQueryResponse)
def ask_rag_endpoint(body: RagQueryRequest):
    """
    RAG質問回答:
    質問文からベクトル検索で関連記事を抽出し、Geminiが根拠記事を元に回答・分析を生成する。
    """
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="質問文を入力してください")
    try:
        embedding = create_embedding(f"検索クエリ: {query}")
        articles = search_similar_articles(embedding, limit=body.limit, threshold=body.threshold)
        rag_result = generate_rag_answer(query, articles)
        return {
            "query": query,
            "answer": rag_result["answer"],
            "key_insights": rag_result["key_insights"],
            "referenced_articles": rag_result["referenced_articles"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG回答の生成に失敗しました: {e}")


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

@app.put("/api/user-context")
def save_user_context_endpoint(body: UserContextResponse):
    try:
        print(f"Saving user context: {body.dict()}")
        return save_user_context(body.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザーコンテクストの保存に失敗しました: {e}")
    
@app.get("/api/user-context")
def get_user_context_endpoint():
    try:
        return get_user_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザーコンテクストの取得に失敗しました: {e}")