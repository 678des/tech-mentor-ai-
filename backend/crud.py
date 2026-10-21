# crud.py
from typing import List, Dict, Set,Any
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