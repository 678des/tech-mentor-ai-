import { useEffect, useState, type FormEvent } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

type UserContext = {
  career_goal: string;
  current_focus: string;
  subjects: string[];
  interests: string[];
  current_situation: string;
  projects: string[];
};

type ContextAdvice = {
  overview: string;
  themes: {
    theme: string;
    why: string;
    article_angles: string[];
    search_queries: string[];
  }[];
  after_reading_choices: string[];
  reminder: string;
};

const emptyContext: UserContext = {
  career_goal: "",
  current_focus: "",
  subjects: [],
  interests: [],
  current_situation: "",
  projects: [],
};

function linesToList(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function SidebarGoals() {
  const [context, setContext] = useState<UserContext>(emptyContext);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [generatingAdvice, setGeneratingAdvice] = useState(false);
  const [advice, setAdvice] = useState<ContextAdvice | null>(null);
  const [adviceError, setAdviceError] = useState("");

  useEffect(() => {
    const loadContext = async () => {
      try {
        const response = await fetch(`${API_URL}/api/user-context`);
        if (!response.ok) throw new Error("ユーザー情報を読み込めませんでした。");
        const data = await response.json();
        setContext({ ...emptyContext, ...data });
      } catch (error) {
        setMessage(
          error instanceof Error ? error.message : "読み込みに失敗しました。",
        );
      } finally {
        setLoading(false);
      }
    };
    void loadContext();
  }, []);

  const persistContext = async (): Promise<UserContext> => {
    const response = await fetch(`${API_URL}/api/user-context`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(context),
    });
    if (!response.ok) throw new Error("保存できませんでした。もう一度お試しください。");
    const savedContext = { ...emptyContext, ...(await response.json()) };
    setContext(savedContext);
    return savedContext;
  };

  const saveContext = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await persistContext();
      setMessage("保存しました。これからの記事評価に反映されます。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存に失敗しました。");
    } finally {
      setSaving(false);
    }
  };

  const createAdvice = async () => {
    setGeneratingAdvice(true);
    setAdviceError("");
    setMessage("");
    try {
      await persistContext();
      const response = await fetch(`${API_URL}/api/user-context/advice`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("提案を作れませんでした。少し待ってから再度お試しください。");
      setAdvice(await response.json());
    } catch (error) {
      setAdviceError(error instanceof Error ? error.message : "提案の作成に失敗しました。");
    } finally {
      setGeneratingAdvice(false);
    }
  };

  const updateText = (field: keyof UserContext, value: string) => {
    setContext((current) => ({
      ...current,
      [field]: field === "subjects" || field === "interests" || field === "projects"
        ? linesToList(value)
        : value,
    }));
  };

  if (loading) return <main className="flex-1 p-6">ユーザー情報を読み込み中…</main>;

  return (
    <main className="flex-1 bg-white p-6">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">あなたのコンテクスト</h1>
        <p className="mt-2 text-sm text-slate-600">
          ここに保存した情報を、新しい記事のスコアリング時にAIへ渡します。記事と無理に結びつけず、関係が薄いものは低く評価するよう指示します。
        </p>

        <form onSubmit={saveContext} className="mt-6 space-y-5">
          <label className="block text-sm font-medium">
            長期的に目指したいこと
            <textarea
              rows={2}
              value={context.career_goal}
              onChange={(event) => updateText("career_goal", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder="例：フルスタックWebエンジニアを目指す"
            />
          </label>

          <label className="block text-sm font-medium">
            今の重点・関心
            <textarea
              rows={3}
              value={context.current_focus}
              onChange={(event) => updateText("current_focus", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder="今気になっていること、学びたいこと"
            />
          </label>

          <label className="block text-sm font-medium">
            興味のあるテーマ（1行に1つ）
            <textarea
              rows={4}
              value={context.interests.join("\n")}
              onChange={(event) => updateText("interests", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder={"TypeScript\nAIとエンジニアのキャリア\nクラウドインフラ"}
            />
          </label>

          <label className="block text-sm font-medium">
            学んでいる科目・技術（1行に1つ）
            <textarea
              rows={4}
              value={context.subjects.join("\n")}
              onChange={(event) => updateText("subjects", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder={"データ構造とアルゴリズム\nPython\nLinux"}
            />
          </label>

          <label className="block text-sm font-medium">
            進行中のプロジェクト（1行に1つ）
            <textarea
              rows={3}
              value={context.projects.join("\n")}
              onChange={(event) => updateText("projects", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder="今取り組んでいる開発や学習"
            />
          </label>

          <label className="block text-sm font-medium">
            情報を読むときの状況や希望（任意）
            <textarea
              rows={3}
              value={context.current_situation}
              onChange={(event) => updateText("current_situation", event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 p-3"
              placeholder="例：不安をあおらず、事実と推測を分けて整理したい"
            />
          </label>

          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "保存中…" : "保存する"}
            </button>
            {message && <p role="status" className="text-sm text-slate-600">{message}</p>}
          </div>
        </form>

        <section className="mt-10 border-t border-slate-200 pt-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">情報との向き合い方を相談する</h2>
              <p className="mt-1 max-w-2xl text-sm text-slate-600">
                保存したコンテクストから、今見るテーマや探す記事の切り口を提案します。具体的な記事を検索する機能ではありません。開発タスクへの結びつけも強制しません。
              </p>
            </div>
            <button
              type="button"
              onClick={() => void createAdvice()}
              disabled={generatingAdvice || saving}
              className="rounded bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {generatingAdvice ? "考えています…" : advice ? "もう一度相談する" : "AIに相談する"}
            </button>
          </div>

          {adviceError && <p role="alert" className="mt-4 text-sm text-red-600">{adviceError}</p>}

          {advice && (
            <div className="mt-6 space-y-5">
              <p className="rounded-lg bg-indigo-50 p-4 text-slate-800">{advice.overview}</p>

              <div className="grid gap-4 md:grid-cols-2">
                {advice.themes.map((item, index) => (
                  <article key={`${item.theme}-${index}`} className="rounded-lg border border-slate-200 p-4">
                    <h3 className="font-semibold">{item.theme}</h3>
                    <p className="mt-2 text-sm text-slate-700">{item.why}</p>
                    <h4 className="mt-4 text-sm font-medium">探す記事の切り口</h4>
                    <ul className="mt-1 list-inside list-disc text-sm text-slate-600">
                      {item.article_angles.map((angle, angleIndex) => <li key={`${angle}-${angleIndex}`}>{angle}</li>)}
                    </ul>
                    <h4 className="mt-4 text-sm font-medium">検索語の案</h4>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {item.search_queries.map((query, queryIndex) => (
                        <span key={`${query}-${queryIndex}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">{query}</span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>

              <div className="rounded-lg border border-slate-200 p-4">
                <h3 className="font-medium">読んだ後は、どれを選んでも大丈夫</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {advice.after_reading_choices.map((choice, index) => (
                    <span key={`${choice}-${index}`} className="rounded-full border border-slate-300 px-3 py-1 text-sm">{choice}</span>
                  ))}
                </div>
                <p className="mt-4 text-sm text-slate-600">{advice.reminder}</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
