import type { ResponseArticle } from "../App";

export function ArticleList({
  articlesData,
}: {
  articlesData: ResponseArticle[];
}) {
  return (
    <main className="flex-1 p-4 bg-white">
      <h1>test</h1>
      <div>
        <h2>📰 本日のおすすめAI要約ニュース</h2>
        <span>全{articlesData?.length || 0} 件</span>
      </div>

      {/* 記事カードの一覧 */}
      <div>
        {articlesData ? (
          articlesData?.map((article) => (
            <article key={article.title} className="border p-4 my-2 rounded">
              <div>
                <span>{article.url}</span>
              </div>
              <h3>{article.title}</h3>
              <p>{article.summary}</p>
              <div>
                <button>AI要約を見る →</button>
                <button>★ お気に入り</button>
              </div>
            </article>
          ))
        ) : (
          <></>
        )}
      </div>
    </main>
  );
}
