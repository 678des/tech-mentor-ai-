import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { useEffect, useState } from "react";
import SideBar from "./components/Sidebar";
import { QiitaSearch } from "./components/QiitaSearch";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

// 1. FastAPIのレスポンス構造に合わせたTypeScriptの型定義
export interface ResponseArticle {
  id: number;
  title: string;
  url: string;
  summary: string;
  save_type: "later" | "important" | "done" | null;
  user_note: string | null;
}

function App() {
  const [articlesData, setArticleData] = useState<ResponseArticle[] | null>(
    null,
  );
  const [importantArticlesData, setImportantArticlesData] = useState<
    ResponseArticle[] | null
  >(null);
  const [activeTab, setActiveTab] = useState<string>("tab1");

  const fetchArticles = async () => {
    try {
      const response = await fetch(`${API_URL}/api/articles`);
      if (!response.ok) {
        throw new Error("記事の取得に失敗しました");
      }
      const data = await response.json();
      // FastAPIが { count: number, articles: ResponseArticle[] } の形で返す前提
      setArticleData(data.articles);
    } catch (error) {
      console.error("Fetch error:", error);
    }
  };
  const fetchImportantArticles = async () => {
    try {
      const response = await fetch(`${API_URL}/api/articles/important`);
      if (!response.ok) {
        throw new Error("記事の取得に失敗しました");
      }
      const data = await response.json();
      // FastAPIが { count: number, articles: ResponseArticle[] } の形で返す前提
      setImportantArticlesData(data.articles);
    } catch (error) {
      console.error("Fetch error:", error);
    }
  };
  useEffect(() => {
    fetchArticles();
    fetchImportantArticles();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col">
      <div className="flex">
        <aside>
          <SideBar activeTab={activeTab} setActiveTab={setActiveTab}></SideBar>
        </aside>
        {
          activeTab === "tab1" && (
            <ArticleList
              articlesData={articlesData ?? []}
              onArticleUpdated={(updatedArticle) => {
                setArticleData(
                  (current) =>
                    current?.map((article) =>
                      article.id === updatedArticle.id
                        ? updatedArticle
                        : article,
                    ) ?? null,
                );
              }}
            />
          )

          // <SidebarGoals />
        }
        {activeTab === "tab2" && <SidebarGoals />}
        {activeTab === "tab3" && (
          <ArticleList
            articlesData={importantArticlesData ?? []}
            showSaveByUrl
            editableTitle
            onArticleAdded={(savedArticle) => {
              setImportantArticlesData((current) => {
                const articles = current ?? [];
                return [
                  savedArticle,
                  ...articles.filter((article) => article.id !== savedArticle.id),
                ];
              });
              setArticleData((current) => {
                if (!current) return current;
                return [
                  savedArticle,
                  ...current.filter((article) => article.id !== savedArticle.id),
                ];
              });
            }}
            onArticleUpdated={(updatedArticle) => {
              setImportantArticlesData(
                (current) =>
                  current
                    ?.map((article) =>
                      article.id === updatedArticle.id
                        ? updatedArticle
                        : article,
                    )
                    .filter((article) => article.save_type === "important") ??
                    null,
              );
            }}
          />
        )}
        {activeTab === "tab4" && <QiitaSearch />}
      </div>
    </div>
  );
}

export default App;
