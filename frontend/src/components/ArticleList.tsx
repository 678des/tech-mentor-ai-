import type { ResponseArticle } from "../App";
import { useState, type FormEvent } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export function ArticleList({
  articlesData,
  onArticleUpdated,
  onArticleAdded,
  showSaveByUrl = false,
  editableTitle = false,
  refreshableSummary = false,
  showRssFetchControls = false,
  onRefreshArticles,
}: {
  articlesData: ResponseArticle[];
  onArticleUpdated: (article: ResponseArticle) => void;
  onArticleAdded?: (article: ResponseArticle) => void;
  showSaveByUrl?: boolean;
  editableTitle?: boolean;
  refreshableSummary?: boolean;
  showRssFetchControls?: boolean;
  onRefreshArticles?: () => Promise<void> | void;
}) {
  const [savingIds, setSavingIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [articleUrl, setArticleUrl] = useState("");
  const [isSavingUrl, setIsSavingUrl] = useState(false);
  const [saveUrlMessage, setSaveUrlMessage] = useState<string | null>(null);
  const [editingTitleId, setEditingTitleId] = useState<number | null>(null);
  const [titleDraft, setTitleDraft] = useState("");
  const [savingTitleId, setSavingTitleId] = useState<number | null>(null);
  const [refreshingSummaryId, setRefreshingSummaryId] = useState<number | null>(null);
  const [summaryMessage, setSummaryMessage] = useState<string | null>(null);

  // RSS取得・AIパイプライン用ステート
  const [isFetchingRss, setIsFetchingRss] = useState(false);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [pipelineMessage, setPipelineMessage] = useState<{
    type: "success" | "error" | "warning";
    text: string;
  } | null>(null);

  const handleFetchRss = async () => {
    setIsFetchingRss(true);
    setError(null);
    setPipelineMessage(null);
    try {
      const response = await fetch(`${API_URL}/api/fetch-rss`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "RSSの取得に失敗しました。");
      }
      setPipelineMessage({
        type: "success",
        text: data.message || `${data.count ?? 0}件の新着記事を取得・保存しました！`,
      });
      if (onRefreshArticles) {
        await onRefreshArticles();
      }
    } catch (err) {
      setPipelineMessage({
        type: "error",
        text: err instanceof Error ? err.message : "RSSの取得に失敗しました。",
      });
    } finally {
      setIsFetchingRss(false);
    }
  };

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true);
    setError(null);
    setPipelineMessage(null);
    try {
      const response = await fetch(`${API_URL}/api/run-pipeline`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "パイプラインの実行に失敗しました。");
      }
      setPipelineMessage({
        type: data.status === "warning" ? "warning" : "success",
        text: data.message || "RSS取得とAI要約が完了しました！",
      });
      if (onRefreshArticles) {
        await onRefreshArticles();
      }
    } catch (err) {
      setPipelineMessage({
        type: "error",
        text: err instanceof Error ? err.message : "パイプラインの実行に失敗しました。",
      });
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const refreshArticleSummary = async (article: ResponseArticle) => {
    setRefreshingSummaryId(article.id);
    setError(null);
    setSummaryMessage(null);
    try {
      const response = await fetch(
        `${API_URL}/api/articles/${article.id}/refresh-summary`,
        { method: "POST" },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "概要を再取得できませんでした。");
      }
      onArticleUpdated(data.article);
      setSummaryMessage(`「${data.article.title}」の概要を更新しました。`);
    } catch (refreshError) {
      setError(
        refreshError instanceof Error
          ? refreshError.message
          : "概要を再取得できませんでした。",
      );
    } finally {
      setRefreshingSummaryId(null);
    }
  };

  const saveArticleTitle = async (article: ResponseArticle) => {
    const title = titleDraft.trim();
    if (!title) {
      setError("タイトルを入力してください。");
      return;
    }
    setSavingTitleId(article.id);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/articles/${article.id}/title`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "タイトルを更新できませんでした。");
      onArticleUpdated(data);
      setEditingTitleId(null);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "タイトルを更新できませんでした。");
    } finally {
      setSavingTitleId(null);
    }
  };

  const saveArticleUrl = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSaveUrlMessage(null);
    setIsSavingUrl(true);
    try {
      const response = await fetch(`${API_URL}/api/articles/save-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: articleUrl.trim() }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "記事を保存できませんでした。");
      }
      onArticleAdded?.(data.article);
      setArticleUrl("");
      setSaveUrlMessage("重要記事に保存しました。");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "記事を保存できませんでした。");
    } finally {
      setIsSavingUrl(false);
    }
  };

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
      {/* デバッグ・プロトタイピング用 RSS取得コントロール */}
      {showRssFetchControls && (
        <section className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <span>🛠️ デバッグ・プロトタイピング操作</span>
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                GitHub Actionsを待たずに、手動でRSS記事の取得やAI評価を実行できます。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => void handleFetchRss()}
                disabled={isFetchingRss || isRunningPipeline}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
              >
                {isFetchingRss ? (
                  <>
                    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>RSS取得中…</span>
                  </>
                ) : (
                  <>
                    <span>📡 RSS即時取得</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => void handleRunPipeline()}
                disabled={isFetchingRss || isRunningPipeline}
                className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
              >
                {isRunningPipeline ? (
                  <>
                    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>一括処理中…</span>
                  </>
                ) : (
                  <>
                    <span>⚡ 一括実行 (RSS取得＋AI要約)</span>
                  </>
                )}
              </button>
            </div>
          </div>
          {pipelineMessage && (
            <div
              role="status"
              className={`mt-3 rounded-lg p-2.5 text-xs font-medium border ${
                pipelineMessage.type === "success"
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                  : pipelineMessage.type === "warning"
                  ? "bg-amber-50 text-amber-800 border-amber-200"
                  : "bg-red-50 text-red-800 border-red-200"
              }`}
            >
              {pipelineMessage.text}
            </div>
          )}
        </section>
      )}

      {showSaveByUrl && (
        <section className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <h2 className="text-lg font-semibold">URLから重要記事を保存</h2>
          <p className="mt-1 text-sm text-slate-600">
            アプリ外で見つけた記事のURLを貼り付けて保存できます。
          </p>
          <form onSubmit={(event) => void saveArticleUrl(event)} className="mt-3 flex flex-col gap-2 sm:flex-row">
            <input
              type="url"
              required
              maxLength={2048}
              value={articleUrl}
              onChange={(event) => setArticleUrl(event.target.value)}
              placeholder="https://example.com/article"
              aria-label="保存する記事のURL"
              className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={isSavingUrl}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSavingUrl ? "保存中…" : "重要記事に保存"}
            </button>
          </form>
          {saveUrlMessage && <p role="status" className="mt-2 text-sm text-emerald-700">{saveUrlMessage}</p>}
        </section>
      )}
      <div className="mb-3">
        <span className="font-semibold text-slate-700">全 {articlesData?.length || 0} 件</span>
      </div>

      {/* 記事カードの一覧 */}
      <div>
        {error && (
          <p role="alert" className="text-sm text-red-600 mb-2">
            {error}
          </p>
        )}
        {summaryMessage && (
          <p role="status" className="text-sm text-emerald-700 mb-2">
            {summaryMessage}
          </p>
        )}
        {articlesData ? (
          articlesData?.map((article) => (
            <article
              key={article.id}
              className="border p-4 my-2 rounded space-y-3"
            >
              <div>
                {editingTitleId === article.id ? (
                  <form
                    className="flex flex-col gap-2 sm:flex-row"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void saveArticleTitle(article);
                    }}
                  >
                    <input
                      autoFocus
                      required
                      maxLength={2048}
                      value={titleDraft}
                      onChange={(event) => setTitleDraft(event.target.value)}
                      aria-label="記事タイトル"
                      className="min-w-0 flex-1 rounded border border-slate-300 px-2 py-1"
                    />
                    <button
                      type="submit"
                      disabled={savingTitleId === article.id}
                      className="rounded bg-blue-600 px-3 py-1 text-sm text-white disabled:opacity-60"
                    >
                      {savingTitleId === article.id ? "保存中…" : "保存"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingTitleId(null)}
                      disabled={savingTitleId === article.id}
                      className="rounded border border-slate-300 px-3 py-1 text-sm"
                    >
                      キャンセル
                    </button>
                  </form>
                ) : (
                  <div className="flex flex-wrap items-center gap-2">
                    <a href={article.url} target="_blank" rel="noreferrer">
                      <h3 className="font-medium text-blue-700 hover:underline">{article.title}</h3>
                    </a>
                    {editableTitle && (
                      <button
                        type="button"
                        onClick={() => {
                          setTitleDraft(article.title);
                          setEditingTitleId(article.id);
                        }}
                        className="text-xs text-slate-500 underline hover:text-slate-800"
                      >
                        タイトルを編集
                      </button>
                    )}
                  </div>
                )}
              </div>
              <p className="text-sm text-slate-600">{article.summary}</p>
              {refreshableSummary && (
                <button
                  type="button"
                  onClick={() => void refreshArticleSummary(article)}
                  disabled={refreshingSummaryId !== null}
                  className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {refreshingSummaryId === article.id ? "取得中…" : "概要を再取得"}
                </button>
              )}
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
