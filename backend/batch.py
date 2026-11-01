from rss import get_news
from crud import vectorize_unembedded_articles


def run_batch_pipeline():
    """
    夜間バッチ（GitHub Actions等）で実行されるRAGパイプライン関数
    RSS新着記事の取得と、未ベクトル化記事の自動Embedding生成（RAGインデックス化）を実行
    """
    print("--- [RAG Batch] 最新記事取得・DB保存開始 ---")
    get_news(auto_vectorize=False)

    print("--- [RAG Batch] 未ベクトル化記事の自動Embedding化開始 ---")
    result = vectorize_unembedded_articles(batch_size=100)
    print(f"--- [RAG Batch] パイプライン完了: {result['processed']}件ベクトル化 ---")


if __name__ == "__main__":
    run_batch_pipeline()
