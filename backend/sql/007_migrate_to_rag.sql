-- 007_migrate_to_rag.sql
-- AIスコアリング・要約処理を停止し、RAG（ベクトル検索・質問回答）に一本化するためのマイグレーションSQL

-- 1. 旧スコアリング関連カラムの削除
ALTER TABLE public.articles
  DROP COLUMN IF EXISTS ai_score,
  DROP COLUMN IF EXISTS ai_comment;

-- 2. 旧ユーザー目標・ロードマップテーブルの削除
DROP TABLE IF EXISTS public.user_context CASCADE;

-- 3. pgvector 拡張機能の有効化（未有効の場合）
CREATE EXTENSION IF NOT EXISTS vector;

-- 4. RAGベクトル類似度検索関数の定義・更新
CREATE OR REPLACE FUNCTION public.match_articles(
  query_embedding vector(1536),
  match_threshold double precision DEFAULT 0.0,
  match_count integer DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  title text,
  url text,
  summary text,
  similarity double precision
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    a.id,
    a.title,
    a.url,
    a.summary,
    (1 - (a.embedding <=> query_embedding))::double precision AS similarity
  FROM public.articles AS a
  WHERE a.embedding IS NOT NULL
    AND 1 - (a.embedding <=> query_embedding) >= match_threshold
  ORDER BY a.embedding <=> query_embedding
  LIMIT GREATEST(match_count, 1);
$$;
