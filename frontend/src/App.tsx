import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { Header } from "./components/Header";
import { useEffect, useState } from "react";
import {
  Sparkles,
  ExternalLink,
  BookOpen,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

// 1. FastAPIのレスポンス構造に合わせたTypeScriptの型定義
interface SelectedArticle {
  title: string;
  url: string;
  reason: string;
}

interface NewsResponse {
  mentor_message: string;
  selected_articles: SelectedArticle[];
  all_candidates_count: number;
}

function App() {
  const [data, setData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = () => {
    setLoading(true);
    setError(null);

    fetch("http://127.0.0.1:8000/api/news")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`サーバーエラー: ${res.status}`);
        }
        return res.json();
      })
      .then((data: NewsResponse) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("API取得エラー:", err);
        setError(
          "データの取得に失敗しました。FastAPIサーバーが起動しているか確認してください。",
        );
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchNews();
  }, []);
  return (
    <div className="flex flex-col h-screen w-full">
      <div className="min-h-screen bg-slate-50 text-slate-800 p-6 md:p-12">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* ヘッダーエリア */}
          <header className="flex items-center justify-between border-b pb-4 border-slate-200">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 flex items-center gap-2">
                <BookOpen className="w-8 h-8 text-indigo-600" />
                Student IT News AI
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                あなた専属のAIメンターが厳選した最新の技術ニュース
              </p>
            </div>
            <button
              onClick={fetchNews}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium rounded-lg shadow-sm transition"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              再取得
            </button>
          </header>

          {/* 1. ローディング状態 */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              <p className="text-slate-600 font-medium">
                RSSフィードを収集し、AIエージェントが記事を分析中...
              </p>
            </div>
          )}

          {/* 2. エラー状態 */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
              <div>
                <p className="font-bold">エラーが発生しました</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* 3. データ読み込み成功時のメイン表示 */}
          {!loading && !error && data && (
            <main className="space-y-6">
              {/* 💬 AIメンターからのアドバイスカード */}
              <section className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-md">
                <div className="flex items-center gap-2 font-bold text-lg mb-2 text-indigo-100">
                  <Sparkles className="w-5 h-5 text-amber-300" />
                  <span>専属AIメンターからのアドバイス</span>
                </div>
                <p className="leading-relaxed text-indigo-50 font-medium whitespace-pre-wrap">
                  {data.mentor_message}
                </p>
              </section>

              {/* 📰 選定記事カード一覧 */}
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-slate-900">
                    今あなたに読んでほしい記事 ({data.selected_articles.length}
                    選)
                  </h2>
                  <span className="text-xs font-semibold px-2.5 py-1 bg-slate-200 text-slate-700 rounded-full">
                    候補 {data.all_candidates_count} 件から分析
                  </span>
                </div>

                <div className="grid gap-4">
                  {data.selected_articles.map((article, index) => (
                    <article
                      key={index}
                      className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition space-y-3"
                    >
                      {/* タイトルとリンクボタン */}
                      <div className="flex items-start justify-between gap-4">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-lg font-bold text-slate-900 hover:text-indigo-600 leading-snug transition flex items-center gap-2 group"
                        >
                          {article.title}
                          <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 shrink-0" />
                        </a>
                      </div>

                      {/* AI選定理由 */}
                      <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-lg text-sm text-slate-700">
                        <p className="font-semibold text-indigo-900 mb-1 flex items-center gap-1.5">
                          <span className="inline-block w-2 h-2 rounded-full bg-indigo-600"></span>
                          なぜ今読むべきか（AI選定理由）
                        </p>
                        <p className="leading-relaxed text-slate-600">
                          {article.reason}
                        </p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </main>
          )}
        </div>
      </div>

      {/* --- 1. ヘッダー --- */}
      <Header />
      <div className="flex">
        {/* 【左】キャリア＆ロードマップ目標 */}
        <SidebarGoals />
        {/* 【右】ニュース記事リスト */}
        <ArticleList />
      </div>
    </div>
  );
}

export default App;
