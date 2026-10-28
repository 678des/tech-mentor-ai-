import { useState, type FormEvent } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");
const PAGE_SIZE = 20;

type QiitaArticle = {
  id: string;
  title: string;
  url: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  author: string;
  likes_count: number;
};

type QiitaSearchResult = {
  articles: QiitaArticle[];
  page: number;
  per_page: number;
  total_count: number | null;
};

export function QiitaSearch() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [result, setResult] = useState<QiitaSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = async (searchQuery: string, page: number) => {
    const normalizedQuery = searchQuery.trim();
    if (!normalizedQuery) {
      setError("探したい技術やテーマを入力してください。");
      return;
    }

    setLoading(true);
    setError("");
    setSubmittedQuery(normalizedQuery);
    try {
      const params = new URLSearchParams({
        q: normalizedQuery,
        page: String(page),
        per_page: String(PAGE_SIZE),
      });
      const response = await fetch(`${API_URL}/api/qiita/search?${params}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Qiita記事を取得できませんでした。");
      }
      setResult(data);
    } catch (searchError) {
      setError(
        searchError instanceof Error
          ? searchError.message
          : "検索に失敗しました。時間をおいて再度お試しください。",
      );
    } finally {
      setLoading(false);
    }
  };

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void search(query, 1);
  };

  const canGoNext = Boolean(
    result &&
      result.page < 100 &&
      result.articles.length === result.per_page &&
      (result.total_count === null ||
        result.page * result.per_page < result.total_count),
  );

  return (
    <main className="min-w-0 flex-1 bg-white p-6">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-semibold">Qiitaの記事を探す</h1>
        <p className="mt-2 text-sm text-slate-600">
          キーワードから、過去の記事も含めてQiitaを検索します。新着フィードとは別に、今の関心に合う記事を探せます。
        </p>

        <form onSubmit={submitSearch} className="mt-5 flex flex-col gap-3 sm:flex-row">
          <label className="sr-only" htmlFor="qiita-query">検索キーワード</label>
          <input
            id="qiita-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            maxLength={200}
            placeholder="例：TypeScript、AIエージェント、キャリア"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-4 py-3"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "検索中…" : "Qiitaを検索"}
          </button>
        </form>

        <p className="mt-2 text-xs text-slate-500">
          Qiita公式APIの検索結果を表示します。記事本文は保存せず、記事ページへ移動して読めます。
        </p>

        {error && <p role="alert" className="mt-5 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        {result && (
          <section aria-live="polite" className="mt-7">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-semibold">「{submittedQuery}」の検索結果</h2>
              <span className="text-sm text-slate-500">
                {result.total_count === null
                  ? `${result.articles.length}件を表示中`
                  : `全${result.total_count.toLocaleString()}件中`}
                {` ${result.page}ページ目`}
              </span>
            </div>

            {result.articles.length === 0 ? (
              <p className="rounded-lg border border-slate-200 p-6 text-slate-600">
                該当する記事が見つかりませんでした。別のキーワードでも検索してみてください。
              </p>
            ) : (
              <div className="space-y-3">
                {result.articles.map((article) => (
                  <article key={article.id} className="rounded-lg border border-slate-200 p-4">
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-lg font-medium text-blue-700 hover:underline"
                    >
                      {article.title}
                    </a>
                    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                      <span>{article.author ? `@${article.author}` : "投稿者不明"}</span>
                      <time dateTime={article.created_at}>
                        投稿日 {new Date(article.created_at).toLocaleDateString("ja-JP")}
                      </time>
                      <span>いいね {article.likes_count}</span>
                    </div>
                    {article.tags.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {article.tags.map((tag) => (
                          <span key={tag} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}

            <nav aria-label="検索結果ページ" className="mt-5 flex items-center justify-between">
              <button
                type="button"
                onClick={() => void search(submittedQuery, result.page - 1)}
                disabled={loading || result.page <= 1}
                className="rounded border border-slate-300 px-4 py-2 text-sm disabled:opacity-40"
              >
                前のページ
              </button>
              <button
                type="button"
                onClick={() => void search(submittedQuery, result.page + 1)}
                disabled={loading || !canGoNext}
                className="rounded border border-slate-300 px-4 py-2 text-sm disabled:opacity-40"
              >
                次のページ
              </button>
            </nav>
          </section>
        )}
      </div>
    </main>
  );
}
