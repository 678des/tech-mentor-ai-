export default function SideBar({
  activeTab,
  setActiveTab,
}: {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}) {
  return (
    <div className="flex flex-col max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-md">
      {/* 2. タブのボタン部分 */}
      <button
        onClick={() => setActiveTab("tab1")}
        className={`flex-1 py-2 text-center font-medium transition-colors ${
          activeTab === "tab1"
            ? "border-b-2 border-blue-500 text-blue-600"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        📰 フィード
      </button>
      <button
        onClick={() => setActiveTab("tab2")}
        className={`flex-1 py-2 text-center font-medium transition-colors ${
          activeTab === "tab2"
            ? "border-b-2 border-blue-500 text-blue-600"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        🎯 目標・ロードマップ
      </button>
      <button
        onClick={() => setActiveTab("tab3")}
        className={`flex-1 py-2 text-center font-medium transition-colors ${
          activeTab === "tab3"
            ? "border-b-2 border-blue-500 text-blue-600"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        保存記事
      </button>
      <button
        onClick={() => setActiveTab("tab4")}
        className={`flex-1 py-2 text-center font-medium transition-colors ${
          activeTab === "tab4"
            ? "border-b-2 border-blue-500 text-blue-600"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        🔎 Qiita検索
      </button>
    </div>
  );
}
