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

  const saveContext = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/user-context`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      });
      if (!response.ok) throw new Error("保存できませんでした。もう一度お試しください。");
      const savedContext = await response.json();
      setContext({ ...emptyContext, ...savedContext });
      setMessage("保存しました。これからの記事評価に反映されます。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存に失敗しました。");
    } finally {
      setSaving(false);
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
      </div>
    </main>
  );
}
