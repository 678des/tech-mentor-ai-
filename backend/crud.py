# crud.py
from typing import List, Dict, Set,Any
from database import supabase

DEFAULT_USER_CONTEXT: Dict[str, Any] = {
    "id": 1,
    "career_goal": "フルスタックWebエンジニアまたはクラウドインフラエンジニアを目指す",
    "current_focus": "情報を集める不安を減らし、自分のペースで学びや開発を続ける",
    "subjects": [],
    "interests": [],
    "current_situation": "技術情報を見て不安に飲まれず、事実を受け止めながら自分のペースで前に進みたい",
    "projects": [],
}


def get_user_context() -> Dict[str, Any]:
    """唯一のユーザーコンテクストを取得する。未作成なら空の初期値を返す。"""
    response = (
        supabase.table("user_context")
        .select("*")
        .eq("id", 1)
        .maybe_single()
        .execute()
    )
    return response.data or DEFAULT_USER_CONTEXT.copy()


def save_user_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """唯一のユーザーコンテクストを作成または更新する。"""
    payload = {**context, "id": 1}
    supabase.table("user_context").upsert(payload, on_conflict="id").execute()
    return get_user_context()

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

def save_articles(articles: List[Dict[str, str]]) -> None:
    """
    記事リスト（dictのリスト）をSupabaseの `articles` テーブルに一括保存する。
    URLの重複防止はDB側のUNIQUE制約（on_conflict="url"）と ignore_duplicates=True で制御。
    """
    if not articles:
        print("保存対象の記事がありません。")
        return

    try:
        # upsert + ignore_duplicates により、URLが重複しているレコードはスキップされます
        response = supabase.table("articles").upsert(
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


def update_article_summary(article_id: int, title: str, summary: str) -> Dict[str, Any] | None:
    response = (
        supabase.table("articles")
        .update({"title": title, "summary": summary, "embedding": None})
        .eq("id", article_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_top_scored_articles() -> List[Dict[str, Any]]:
    """
    Supabaseの `articles` テーブルから、ai_score の高い順に上位20件の記事を取得する。
    ai_scoreが設定されていない記事を除外したい場合は .not_.is_("ai_score", "null") を挟む。
    """
    try:
        response = supabase.table("articles").select("*").order("ai_score", desc=True).limit(20).execute()
        return response.data
    except Exception as e:
        print(f"記事全件取得時にエラーが発生しました: {e}")
        return []


def get_unprocessed_articles() -> List[Dict[str, Any]]:
    """
    Supabaseの `articles` テーブルから、まだAIスコアがついていない（ai_scoreがNULLの）記事を取得する。
    """
    try:
        # ai_score が is.null のものを取得（未処理のものだけを効率よく処理する）
        response = (
            supabase.table("articles")
            .select("id, title, ai_comment, summary")
            .is_("ai_score", "null")
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"未処理記事の取得時にエラーが発生しました: {e}")
        return []


def get_important_articles():
    response = (
        supabase.table("articles")
        .select("*")
        .eq("save_type", "important")
        .order("ai_score", desc=True)
        .execute()
    )
    return response.data


def update_articles_in_supabase(evaluated_results: List[Dict[str, Any]]):
    """
    Geminiから返ってきた評価結果（スコア・コメント）をSupabaseに一括反映する。
    """
    for item in evaluated_results:
        article_id = item.get("id")
        score = item.get("score")
        comment = item.get("comment")

        if article_id is None:
            continue

        try:
            supabase.table("articles").update({
                "ai_score": score,
                "ai_comment": comment
            }).eq("id", article_id).execute()
            print(f"記事ID {article_id}: 更新成功 (Score: {score})")
        except Exception as e:
            print(f"記事ID {article_id} のDB更新に失敗しました: {e}")


def update_article_user_state(
    article_id: int,
    save_type: str | None,
    user_note: str | None,
) -> Dict[str, Any] | None:
    """試作用に記事の保存タイプと自分用メモを更新する。"""
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
