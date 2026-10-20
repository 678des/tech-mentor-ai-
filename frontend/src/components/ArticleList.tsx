import { useState } from "react";
const DUMMY_ARTICLES = [
  {
    id: "1",
    title: "React 19の新機能とServer Actionsの実践的な使い方",
    summary:
      "React 19で導入される非同期処理の改善や、Form処理を簡略化するServer Actionsの活用例について解説。",
    category: "フロントエンド",
    date: "10分前",
  },
  {
    id: "2",
    title: "Python + Gemini APIで作る自分専用の自動化パイプライン",
    summary:
      "LLMを使った日常タスクの自動化スクリプトの構築手順。環境変数管理からエラーハンドリングまで網羅。",
    category: "AI / バックエンド",
    date: "1時間前",
  },
  {
    id: "3",
    title: "Vite 5.0による開発環境の高速化とトラブルシューティング",
    summary:
      "従来のWebpackからViteへ移行する際の注意点と、ESMモジュールを活用した爆速ビルドの仕組み。",
    category: "開発ツール",
    date: "3時間前",
  },
  {
    id: "4",
    title: "GitHub Actionsを用いたCI/CD構築の基礎",
    summary:
      "リポジトリへのPushをトリガーに、自動テストとデプロイを自動化するパイプラインの書き方。",
    category: "DevOps",
    date: "5時間前",
  },
];

export function ArticleList() {
  const [articles] = useState(DUMMY_ARTICLES);
  return (
    <main className="flex-1 p-4 bg-white">
      <h1>test</h1>
      <div>
        <h2>📰 本日のおすすめAI要約ニュース</h2>
        <span>全 {articles.length} 件</span>
      </div>

      {/* 記事カードの一覧 */}
      <div>
        {articles.map((article) => (
          <article key={article.id}>
            <div>
              <span>{article.category}</span>
              <span>{article.date}</span>
            </div>
            <h3>{article.title}</h3>
            <p>{article.summary}</p>
            <div>
              <span>AI要約を見る →</span>
              <button>★ お気に入り</button>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
