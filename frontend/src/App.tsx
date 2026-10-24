import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { Header } from "./components/Header";
import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import SideBar from "./components/Sidebar";

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
  const [activeTab, setActiveTab] = useState<string>("tab1");

  const fetchScoring = async () => {
    try {
      const response = await fetch(`${API_URL}api/run-ai-pipeline`, {
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
      const response = await fetch(`${API_URL}api/articles`);
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
      {/* <header className="flex items-center justify-between border-b pb-4 border-slate-200">
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
      </header> */}

      {/* --- 1. ヘッダー --- */}
      {/* <Header /> */}
      <div className="flex">
        <aside>
          <SideBar activeTab={activeTab} setActiveTab={setActiveTab}></SideBar>
        </aside>
        {activeTab === "tab1" ? (
          <ArticleList articlesData={articlesData ?? []} />
        ) : (
          <SidebarGoals />
        )}
      </div>
    </div>
  );
}

export default App;
