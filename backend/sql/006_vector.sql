-- If you already created this column in Supabase, skip this ALTER statement.
alter table articles add column if not exists embedding vector(1536);

-- Similarity search used by POST /api/articles/vector-search.
-- Run this file once in the Supabase SQL Editor. If the embedding column already
-- exists, this file is safe to run again because the column is IF NOT EXISTS.
create or replace function public.match_articles(
  query_embedding vector(1536),
  match_threshold double precision default 0,
  match_count integer default 10
)
returns table (
  id bigint,
  title text,
  url text,
  summary text,
  similarity double precision
)
language sql
stable
as $$
  select
    a.id,
    a.title,
    a.url,
    a.summary,
    (1 - (a.embedding <=> query_embedding))::double precision as similarity
  from public.articles as a
  where a.embedding is not null
    and 1 - (a.embedding <=> query_embedding) >= match_threshold
  order by a.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;
