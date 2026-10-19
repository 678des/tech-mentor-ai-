# TechMentor AI 🚀

情報過多による焦りを排除し、開発に没頭するための**「AI駆動型パーソナライズRSSニュース収集・要約ツール」**です。

自分の興味や大学の履修科目、現在のモチベーションや状況に合わせて、AI（Gemini API）が最新の技術トレンド記事を自動選定・深掘り要約してくれます。

---

## 🏗️ アーキテクチャ・プロジェクト構成

本プロジェクトは、**Pythonバックエンド**と**React (Vite/TypeScript) フロントエンド**の分離構成で構築されています。

```text
student-it-news-ai/
 ┣ 📂 backend/        # Python (RSS収集、Qiita API連携、Gemini AI解析)
 ┃   ┣ 📜 main.py
 ┃   ┣ 📜 requirements.txt
 ┃   └ 📜 .env
 ┣ 📂 frontend/       # React + TypeScript + Vite (UI・ダッシュボード)
 ┃   ┣ 📜 package.json
 ┃   ┣ 📜 vite.config.ts
 ┃   └ 📜 .env
 ┣ 📜 .gitignore
 ┗ 📜 README.md
```

---

## 🛠️ 技術スタック

### Backend (Python)

- **Python / feedparser**: RSSフィードの取得とパース
- **Qiita API (v2)**: 記事IDからの安全な本文（Markdown）取得
- **Google Gemini API**: 記事の分析・モチベーションに寄り添うメンター的要約の生成
- **python-dotenv**: 環境変数のセキュアな管理

### Frontend (React)

- **React + TypeScript + Vite**: 高速で快適なSPA（シングルページアプリケーション）開発環境
- **Lucide React (推奨)**: シンプルで美しいUIアイコン
- **Tailwind CSS (推奨)**: スタイリング

---

## 🚀 起動方法（ローカル環境）

### 1. バックエンド（Python）の起動

```bash
# backend フォルダに移動
cd backend

# 仮想環境の作成と有効化
python -m venv venv

# Windowsの場合:
.\venv\Scripts\activate
# macOS/Linuxの場合:
# source venv/bin/activate

# 依存ライブラリのインストール
pip install -r requirements.txt
pip install python-dotenv

# .env ファイルを作成し、GEMINI_API_KEYを設定する
# 例: GEMINI_API_KEY="your-api-key"

# スクリプトの実行
python main.py
```

### 2. フロントエンド（React / Vite）の起動

```bash
# 別ターミナルを開き、frontend フォルダに移動
cd frontend

# 依存パッケージのインストール
npm install

# 開発サーバーの起動
npm run dev
```

---

## 💡 今後の開発目標

- [ ] 記事一覧と要約詳細モーダルのUI実装
- [ ] バックエンド（Python）とフロントエンド（React）のAPI連携
- [ ] お気に入り・保存済み記事のタブ切り替え機能
