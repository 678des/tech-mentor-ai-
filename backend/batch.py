from ai import evaluate_articles_with_gemini
from crud import get_unprocessed_articles, get_user_context, update_articles_in_supabase
from rss import get_news

def run_batch_pipeline():

    """
    夜間バッチなどで実行されるメインのパイプライン関数
    """
    
    print("--- 最新記事取得・DB保存開始 ---")
    get_news()
    
    print("--- AI要約・スコアリングバッチ開始 ---")
    
    # 1. 未処理の記事を取得
    unprocessed = get_unprocessed_articles()
    if not unprocessed:
        print("処理対象の新着記事はありません。")
        return

    print(f"{len(unprocessed)}件の未処理記事を検出しました。Geminiへ送信します...")

    # 2. まとめてGeminiに評価させる（バッチ処理）
    user_context = get_user_context()
    evaluated = evaluate_articles_with_gemini(unprocessed, user_context)
    if not evaluated:
        print("Geminiからの評価結果を取得できませんでした。")
        return

    # 3. Supabaseを更新
    update_articles_in_supabase(evaluated)
    print("--- AI要約・スコアリングバッチ完了 ---")

if __name__ == "__main__":
    run_batch_pipeline()
