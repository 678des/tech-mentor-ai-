import type { ResponseArticle } from "../App";
import { useState } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export function ArticleList({
  articlesData,
  onArticleUpdated,
}: {
  articlesData: ResponseArticle[];
  onArticleUpdated: (article: ResponseArticle) => void;
}) {
  const [savingIds, setSavingIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  const saveArticleState = async (
    article: ResponseArticle,
    save_type: ResponseArticle["save_type"],
    user_note: string,
  ) => {
    setSavingIds((ids) => [...ids, article.id]);
    setError(null);
    try {
      const response = await fetch(
        `${API_URL}/api/articles/${article.id}/user-state`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ save_type, user_note: user_note || null }),
        },
      );
      if (!response.ok)
        throw new Error("保存できませんでした。もう一度お試しください。");
      onArticleUpdated(await response.json());
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "保存に失敗しました。",
      );
    } finally {
      setSavingIds((ids) => ids.filter((id) => id !== article.id));
    }
  };

  return (
    <main className="flex-1 p-4 bg-white">
      <div>
        <span>全{articlesData?.length || 0} 件</span>
      </div>

      {/* 記事カードの一覧 */}
      <div>
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        {articlesData ? (
          articlesData?.map((article) => (
            <article
              key={article.id}
              className="border p-4 my-2 rounded space-y-3"
            >
              <div>
                <a href={article.url}>
                  <h3>{article.title}</h3>
                </a>
              </div>
              <p className="text-sm text-slate-600">{article.summary}</p>
              <div className="flex flex-wrap items-center gap-2">
                <label className="text-sm" htmlFor={`save-type-${article.id}`}>
                  保存タイプ
                </label>
                <select
                  id={`save-type-${article.id}`}
                  value={article.save_type ?? ""}
                  disabled={savingIds.includes(article.id)}
                  onChange={(event) =>
                    void saveArticleState(
                      article,
                      (event.target.value ||
                        null) as ResponseArticle["save_type"],
                      article.user_note ?? "",
                    )
                  }
                  className="rounded border border-slate-300 px-2 py-1 text-sm"
                >
                  <option value="">未処理</option>
                  <option value="important">参考記事として保存</option>
                  <option value="later">保留(AI要約)</option>
                  <option value="done">完了</option>
                </select>
                {savingIds.includes(article.id) && (
                  <span className="text-xs text-slate-500">保存中…</span>
                )}
              </div>
              <label className="block text-sm">
                自分のメモ
                <textarea
                  key={`${article.id}-${article.user_note ?? ""}`}
                  defaultValue={article.user_note ?? ""}
                  rows={2}
                  maxLength={2000}
                  placeholder="残しておきたい感想や理由（任意）"
                  className="mt-1 w-full rounded border border-slate-300 p-2"
                  onBlur={(event) => {
                    if (event.target.value !== (article.user_note ?? "")) {
                      void saveArticleState(
                        article,
                        article.save_type,
                        event.target.value,
                      );
                    }
                  }}
                  disabled={savingIds.includes(article.id)}
                />
              </label>
            </article>
          ))
        ) : (
          <></>
        )}
      </div>
    </main>
  );
}
