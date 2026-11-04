# crud.py
from typing import List, Dict, Set, Any
from database import supabase


def get_all_urls() -> Set[str]:
    """
    Supabaseの `articles` テーブルに保存されている全記事のURLを取得する。
    重複記事の判定用に使用。
    """
    try:
        response = supabase.table("articles").select("url").execute()
        urls = {row["url"] for row in response.data}
        return urls
    except Exception as e:
        print(f"URL取得時にエラーが発生しました: {e}")
        return set()


def save_articles(articles: List[Dict[str, Any]]) -> None:
    """
    記事リスト（dictのリスト）をSupabaseの `articles` テーブルに一括保存する。
    URLの重複防止はDB側のUNIQUE制約（on_conflict="url"）と ignore_duplicates=True で制御。
    """
    if not articles:
        print("保存対象の記事がありません。")
        return

    try:
        supabase.table("articles").upsert(
            articles,
            on_conflict="url",
            ignore_duplicates=True
        ).execute()
        print(f"✅ {len(articles)} 件の記事保存処理を実行しました。")
    except Exception as e:
        print(f"記事保存時にエラーが発生しました: {e}")


def get_article_by_id(article_id: int) -> Dict[str, Any] | None:
    response = (
        supabase.table("articles")
        .select("id, title, url, summary")
        .eq("id", article_id)
        .maybe_single()
        .execute()
    )
    return response.data


def save_article_url_as_important(url: str, title: str) -> Dict[str, Any]:
    """Save a user-provided HTTPS URL to the important articles list."""
    article_fields = "id, title, url, summary, save_type, user_note, created_at"
    lookup = (
        supabase.table("articles")
        .select(article_fields)
        .eq("url", url)
        .limit(1)
        .execute()
    )
    existing_rows = getattr(lookup, "data", None) or []
    existing = existing_rows[0] if existing_rows else None

    if existing:
        (
            supabase.table("articles")
            .update({"save_type": "important"})
            .eq("id", existing["id"])
            .execute()
        )
        refreshed = (
            supabase.table("articles")
            .select(article_fields)
            .eq("id", existing["id"])
            .limit(1)
            .execute()
        )
        rows = getattr(refreshed, "data", None) or []
        return rows[0] if rows else {**existing, "save_type": "important"}

    (
        supabase.table("articles")
        .insert({
            "title": title,
            "url": url,
            "summary": "",
            "save_type": "important",
        })
        .execute()
    )
    saved = (
        supabase.table("articles")
        .select(article_fields)
        .eq("url", url)
        .limit(1)
        .execute()
    )
    saved_rows = getattr(saved, "data", None) or []
    if not saved_rows:
        raise RuntimeError("記事を保存できませんでした")
    return saved_rows[0]


def update_article_title(article_id: int, title: str) -> Dict[str, Any] | None:
    """Update an article title and invalidate its embedding for later rebuilding."""
    (
        supabase.table("articles")
        .update({"title": title, "embedding": None})
        .eq("id", article_id)
        .execute()
    )
    response = (
        supabase.table("articles")
        .select("id, title, url, summary, save_type, user_note, created_at")
        .eq("id", article_id)
        .limit(1)
        .execute()
    )
    rows = getattr(response, "data", None) or []
    if not rows:
        return None
    article = rows[0]
    article.pop("embedding", None)
    return article


def get_articles(limit: int = 100, unhandled_only: bool = True) -> List[Dict[str, Any]]:
    """
    Supabaseの `articles` テーブルから、最新順（created_at desc）で最大100件取得する。
    """
    try:
        query = supabase.table("articles").select("*")
        if unhandled_only:
            query = query.is_("save_type", "null")
        response = (
            query
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"記事取得時にエラーが発生しました: {e}")
        return []


def get_top_scored_articles(limit: int = 100, unhandled_only: bool = True) -> List[Dict[str, Any]]:
    """互換性のためのエイリアス。最新順で取得する。"""
    return get_articles(limit=limit, unhandled_only=unhandled_only)


def get_important_articles() -> List[Dict[str, Any]]:
    try:
        response = (
            supabase.table("articles")
            .select("*")
            .eq("save_type", "important")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"重要記事取得時にエラーが発生しました: {e}")
        return []


def update_article_user_state(
    article_id: int,
    save_type: str | None,
    user_note: str | None,
) -> Dict[str, Any] | None:
    """記事の保存タイプと自分用メモを更新する。"""
    response = (
        supabase.table("articles")
        .update({"save_type": save_type, "user_note": user_note})
        .eq("id", article_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_articles_for_embedding(rebuild: bool = False) -> List[Dict[str, Any]]:
    """Get articles needing embeddings, or all articles when rebuilding."""
    query = (
        supabase.table("articles")
        .select("id, title, summary, url, embedding")
        .order("id")
    )
    if not rebuild:
        query = query.is_("embedding", "null")
    response = query.execute()
    return response.data or []


def save_article_embedding(article_id: int, embedding: List[float]) -> None:
    supabase.table("articles").update({"embedding": embedding}).eq("id", article_id).execute()


def search_similar_articles(
    embedding: List[float], limit: int = 10, threshold: float = 0.0
) -> List[Dict[str, Any]]:
    response = supabase.rpc(
        "match_articles",
        {
            "query_embedding": embedding,
            "match_threshold": threshold,
            "match_count": limit,
        },
    ).execute()
    return response.data or []


def vectorize_unembedded_articles(batch_size: int = 50) -> Dict[str, Any]:
    """
    未ベクトル化の記事を自動検出して Gemini Embedding を生成・保存する。
    RAGパイプラインの自動化処理として利用。
    """
    from ai import build_article_embedding_text, create_embedding

    pending = get_articles_for_embedding(rebuild=False)[:batch_size]
    if not pending:
        return {"processed": 0, "failed_ids": []}

    processed = 0
    failed_ids = []
    for article in pending:
        article_id = article["id"]
        try:
            embed_text = build_article_embedding_text(article)
            if not embed_text.strip():
                continue
            embedding = create_embedding(embed_text)
            save_article_embedding(article_id, embedding)
            processed += 1
        except Exception as e:
            print(f"記事ID {article_id} のベクトル化に失敗: {e}")
            failed_ids.append(article_id)

    print(f"✅ {processed} 件の記事をベクトル化しました（失敗: {len(failed_ids)} 件）")
    return {"processed": processed, "failed_ids": failed_ids}



def get_user_context() -> Dict[str, Any]:
    """唯一のユーザーコンテクストを取得する。未作成なら空の初期値を返す。"""
    print("Fetching user context from Supabase...")
    
    response = (
        supabase.table("user_context")
        .select("career_goal, current_focus, current_situation, interests, projects, subjects")
        .eq("id", 1)
        .maybe_single()
        .execute()
    )
    return response.data 



def save_user_context(context: Dict[str, Any]):
    """唯一のユーザーコンテクストを作成または更新する。"""
    print(f"Saving user context: {context}")
    payload = {**context, "id": 1}
    try:
        supabase.table("user_context").upsert(payload, on_conflict="id").execute()
        return get_user_context()
    except Exception as e:
        print(f"Error saving user context: {e}")
    
