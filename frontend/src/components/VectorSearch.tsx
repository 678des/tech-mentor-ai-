import { useState, type FormEvent } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

type VectorArticle = {
  id: number;
  title: string;
  url: string;
  summary: string | null;
  similarity: number;
};

type VectorSearchResponse = {
  query: string;
  count: number;
  articles: VectorArticle[];
};

export function VectorSearch() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<VectorSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedQuery = query.trim();
    if (!normalizedQuery) {
      setError("探したいテーマや疑問を入力してください。");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/api/articles/vector-search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: normalizedQuery, limit: 20 }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "記事を検索できませんでした。");
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

  return (
    <main className="min-w-0 flex-1 bg-white p-6">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-semibold">保存済み記事を意味で探す</h1>
        <p className="mt-2 text-sm text-slate-600">
          DBに保存した記事から、入力したテーマに意味が近いものを探します。単語が一致しなくても、内容が近い記事が見つかることがあります。
        </p>

        <form onSubmit={(event) => void search(event)} className="mt-5 flex flex-col gap-3 sm:flex-row">
          <label className="sr-only" htmlFor="vector-search-query">検索したいテーマや疑問</label>
          <input
            id="vector-search-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            maxLength={1000}
            placeholder="例：個人開発を続ける上で参考になる考え方"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-4 py-3"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "検索中…" : "保存済み記事を検索"}
          </button>
        </form>

        <p className="mt-2 text-xs text-slate-500">
          ベクトル登録済みの記事が検索対象です。概要やタイトルを更新した記事、新しくURL保存した記事は、ベクトル化後に検索できます。
        </p>

        {error && <p role="alert" className="mt-5 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        {result && (
          <section aria-live="polite" className="mt-7">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-semibold">「{result.query}」の検索結果</h2>
              <span className="text-sm text-slate-500">{result.count}件</span>
            </div>

            {result.articles.length === 0 ? (
              <p className="rounded-lg border border-slate-200 p-6 text-slate-600">
                関連する記事が見つかりませんでした。別の表現で試すか、記事がベクトル化されているか確認してください。
              </p>
            ) : (
              <div className="space-y-3">
                {result.articles.map((article) => (
                  <article key={article.id} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-lg font-medium text-blue-700 hover:underline"
                      >
                        {article.title}
                      </a>
                      <span className="shrink-0 rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-700">
                        類似度 {Math.round(article.similarity * 100)}%
                      </span>
                    </div>
                    {article.summary && (
                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">
                        {article.summary}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
