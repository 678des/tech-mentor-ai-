import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { Header } from "./components/Header";
import { useEffect, useState } from "react";
import { BookOpen, RefreshCw } from "lucide-react";

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
  //const [error, setError] = useState<string | null>(null);

  const fetchNews = () => {
    setLoading(true);
    //setError(null);

    console.log("ニュースをフェッチします");
    fetch("http://127.0.0.1:8000/api/news")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`サーバーエラー: ${res.status}`);
        }
        return res.json();
      })
      .then((data: ResponseArticle[]) => {
        setArticleData(data);
        console.log("取得したdata", data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("API取得エラー:", err);
        //setError("データの取得に失敗しました。");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchNews();
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
          onClick={fetchNews}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium rounded-lg shadow-sm transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          再取得
        </button>
      </header>

      {/* 1. ローディング状態 */}
      {/* {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              <p className="text-slate-600 font-medium">
                RSSフィードを収集中...
              </p>
            </div>
          )} */}

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
