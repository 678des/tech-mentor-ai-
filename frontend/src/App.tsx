import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { Header } from "./components/Header";
import { useEffect, useState } from "react";
import { BookOpen, RefreshCw } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// 1. FastAPIのレスポンス構造に合わせたTypeScriptの型定義
export interface ResponseArticle {
  title: string;
  url: string;
  summary: string;
}

function App() {
  const [articlesData, setArticleData] = useState<ResponseArticle[] | null>(
    null,
  );
  const [loading, setLoading] = useState<boolean>(true);

  const fetchScoring = async () => {
    try {
      const response = await fetch(`${API_URL}/api/run-ai-pipeline`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error("記事のスコアリングに失敗しました");
      }
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setLoading(false);
    }
  };
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/articles`);
      if (!response.ok) {
        throw new Error("記事の取得に失敗しました");
      }
      const data = await response.json();
      // FastAPIが { count: number, articles: ResponseArticle[] } の形で返す前提
      setArticleData(data.articles);
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchArticles();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col">
      {/* ヘッダーエリア */}
      <header className="flex items-center justify-between border-b pb-4 border-slate-200">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-8 h-8 text-indigo-600" />
            IT News for Student
          </h1>
          <p className="text-sm text-slate-500 mt-1">最新の技術ニュース</p>
        </div>
        <button
          onClick={fetchArticles}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium rounded-lg shadow-sm transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          再取得
        </button>
        <button
          onClick={fetchScoring}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium rounded-lg shadow-sm transition"
        >
          テストスコアリング
        </button>
      </header>

      {/* --- 1. ヘッダー --- */}
      <Header />
      <div className="flex">
        {/* 【左】キャリア＆ロードマップ目標 */}
        <SidebarGoals />
        {/* 【右】ニュース記事リスト */}
        <ArticleList articlesData={articlesData ?? []} />
      </div>
    </div>
  );
}

export default App;
