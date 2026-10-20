import { SidebarGoals } from "./components/SidebarGoals";
import { ArticleList } from "./components/ArticleList";
import { Header } from "./components/Header";
function App() {
  return (
    <div className="flex flex-col h-screen w-full">
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
